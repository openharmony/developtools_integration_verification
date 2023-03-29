/*
 * Copyright (c) 2022 Huawei Device Co., Ltd.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package dayu200

import (
	"context"
	"errors"
	"fmt"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

var partList = []string{"boot_linux", "system", "vendor", "userdata", "resource", "ramdisk", "chipset", "sys-prod", "chip-prod", "updater"}

// All timeouts are calculated on normal cases, we do not certain that timeouts are enough if some sleeps canceled.
// So simply we do not cancel any Sleep(). TODO: use utils.SleepContext() instead.
func (m *Manager) flashDevice(device string, pkg string, ctx context.Context) error {
	if err := utils.TryRebootToLoader(device, ctx); err != nil {
		return err
	}
	if err := m.flashImages(device, pkg, ctx); err != nil {
		return err
	}
	time.Sleep(20 * time.Second) // usually, it takes about 20s to reboot into OpenHarmony
	if connected := utils.WaitHDC(device, ctx); !connected {
		logrus.Errorf("flash device %s done, but boot unnormally, hdc connection fail", device)
		return fmt.Errorf("flash device %s done, but boot unnormally, hdc connection fail", device)
	}
	time.Sleep(10 * time.Second) // wait 10s more to ensure system has been started completely
	logrus.Infof("flash device %s successfully", device)
	return nil
}

func (m *Manager) flashImages(device string, pkg string, ctx context.Context) error {
	logrus.Infof("calling flash tool to flash %s into %s...", pkg, device)
	locationID := m.locations[device]
	if locationID == "" {
		data, _ := utils.ExecCombinedOutputContext(ctx, m.FlashTool, "LD")
		locationID = strings.TrimPrefix(regexp.MustCompile(`LocationID=\d+`).FindString(string(data)), "LocationID=")
		if locationID == "" {
			time.Sleep(5 * time.Second)
			data, _ := utils.ExecCombinedOutputContext(ctx, m.FlashTool, "LD")
			locationID = strings.TrimPrefix(regexp.MustCompile(`LocationID=\d+`).FindString(string(data)), "LocationID=")
		}
	}
	logrus.Infof("locationID of %s is [%s]", device, locationID)
	if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "UL", filepath.Join(m.Workspace, pkg, "MiniLoaderAll.bin"), "-noreset"); err != nil {
		if errors.Is(err, context.Canceled) {
			return err
		}
		logrus.Errorf("flash MiniLoaderAll.bin fail: %v", err)
		time.Sleep(5 * time.Second)
		if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "UL", filepath.Join(m.Workspace, pkg, "MiniLoaderAll.bin"), "-noreset"); err != nil {
			if errors.Is(err, context.Canceled) {
				return err
			}
			logrus.Errorf("flash MiniLoaderAll.bin fail: %v", err)
			return err
		}
	}
	time.Sleep(3 * time.Second)
	if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "DI", "-p", filepath.Join(m.Workspace, pkg, "parameter.txt")); err != nil {
		if errors.Is(err, context.Canceled) {
			return err
		}
		logrus.Errorf("flash parameter.txt fail: %v", err)
		return err
	}
	time.Sleep(5 * time.Second)
	if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "DI", "-uboot", filepath.Join(m.Workspace, pkg, "uboot.img"), filepath.Join(m.Workspace, pkg, "parameter.txt")); err != nil {
		if errors.Is(err, context.Canceled) {
			return err
		}
		logrus.Errorf("flash device fail: %v", err)
		return err
	}
	time.Sleep(5 * time.Second)
	for _, part := range partList {
		if _, err := os.Stat(filepath.Join(m.Workspace, pkg, part+".img")); err != nil {
			if os.IsNotExist(err) {
				logrus.Infof("part %s.img not exist, ignored", part)
				continue
			}
			return err
		}
		if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "DI", "-"+part, filepath.Join(m.Workspace, pkg, part+".img"), filepath.Join(m.Workspace, pkg, "parameter.txt")); err != nil {
			if errors.Is(err, context.Canceled) {
				return err
			}
			logrus.Errorf("flash device fail: %v", err)
			logrus.Warnf("try again...")
			if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "DI", "-"+part, filepath.Join(m.Workspace, pkg, part+".img"), filepath.Join(m.Workspace, pkg, "parameter.txt")); err != nil {
				if errors.Is(err, context.Canceled) {
					return err
				}
				logrus.Errorf("flash device fail: %v", err)
				return err
			}
		}
		time.Sleep(3 * time.Second)
	}
	time.Sleep(5 * time.Second) // sleep a while for writing
	if err := utils.ExecContext(ctx, m.FlashTool, "-s", locationID, "RD"); err != nil {
		if errors.Is(err, context.Canceled) {
			return err
		}
		return fmt.Errorf("reboot device fail: %v", err)
	}
	return nil
}
