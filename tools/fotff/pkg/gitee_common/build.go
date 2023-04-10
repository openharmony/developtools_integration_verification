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

package gitee_common

import (
	"context"
	"fmt"
	"fotff/res"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"os"
	"path/filepath"
)

type BuildConfig struct {
	Pkg           string
	PreCompileCMD string
	CompileCMD    string
	ImgList       []string
}

func (m *Manager) Build(config BuildConfig, ctx context.Context) error {
	if m.PkgAvailable(config) {
		return nil
	}
	logrus.Infof("%s is not available", config.Pkg)
	err := m.BuildNoRetry(config, false, ctx)
	if err == nil {
		return nil
	}
	logrus.Errorf("build pkg %s err: %v", config.Pkg, err)
	logrus.Infof("rm out and build pkg %s again...", config.Pkg)
	err = m.BuildNoRetry(config, true, ctx)
	if err == nil {
		return nil
	}
	logrus.Errorf("build pkg %s err: %v", config.Pkg, err)
	return err
}

// PkgAvailable returns true if all necessary images are all available to flash.
func (m *Manager) PkgAvailable(config BuildConfig) bool {
	for _, img := range config.ImgList {
		imgName := filepath.Base(img)
		if _, err := os.Stat(filepath.Join(m.Workspace, config.Pkg, imgName)); err != nil {
			return false
		}
	}
	return true
}

// BuildNoRetry obtain an available server, download corresponding codes, and run compile commands
// to build the corresponding package images, then transfer these images to the 'pkg' directory.
func (m *Manager) BuildNoRetry(config BuildConfig, rm bool, ctx context.Context) error {
	logrus.Infof("now Build %s", config.Pkg)
	server := res.GetBuildServer()
	defer res.ReleaseBuildServer(server)
	cmd := fmt.Sprintf("mkdir -p %s && cd %s && repo init -u https://gitee.com/openharmony/manifest.git", server.WorkSpace, server.WorkSpace)
	if err := utils.RunCmdViaSSHContext(ctx, server.Addr, server.User, server.Passwd, cmd); err != nil {
		return fmt.Errorf("remote: mkdir error: %w", err)
	}
	if err := utils.TransFileViaSSH(utils.Upload, server.Addr, server.User, server.Passwd,
		fmt.Sprintf("%s/.repo/manifest.xml", server.WorkSpace), filepath.Join(m.Workspace, config.Pkg, "manifest_tag.xml")); err != nil {
		return fmt.Errorf("upload and replace manifest error: %w", err)
	}
	// 'git lfs install' may fail due to some git hooks. Call 'git lfs update --force' before install to avoid this situation.
	cmd = fmt.Sprintf("cd %s && repo sync -c --no-tags --force-remove-dirty && repo forall -c 'git reset --hard && git clean -dfx && git lfs update --force && git lfs install && git lfs pull'", server.WorkSpace)
	if err := utils.RunCmdViaSSHContext(ctx, server.Addr, server.User, server.Passwd, cmd); err != nil {
		return fmt.Errorf("remote: repo sync error: %w", err)
	}
	cmd = fmt.Sprintf("cd %s && %s", server.WorkSpace, config.PreCompileCMD)
	if err := utils.RunCmdViaSSHContextNoRetry(ctx, server.Addr, server.User, server.Passwd, cmd); err != nil {
		return fmt.Errorf("remote: pre-compile command error: %w", err)
	}
	if rm {
		cmd = fmt.Sprintf("cd %s && rm -rf out", server.WorkSpace)
		if err := utils.RunCmdViaSSHContext(ctx, server.Addr, server.User, server.Passwd, cmd); err != nil {
			return fmt.Errorf("remote: rm ./out command error: %w", err)
		}
	}
	cmd = fmt.Sprintf("cd %s && %s", server.WorkSpace, config.CompileCMD)
	if err := utils.RunCmdViaSSHContextNoRetry(ctx, server.Addr, server.User, server.Passwd, cmd); err != nil {
		return fmt.Errorf("remote: compile command error: %w", err)
	}
	// has been built already, pitiful if canceled, so continue copying
	for _, f := range config.ImgList {
		imgName := filepath.Base(f)
		if err := utils.TransFileViaSSH(utils.Download, server.Addr, server.User, server.Passwd,
			fmt.Sprintf("%s/%s", server.WorkSpace, f), filepath.Join(m.Workspace, config.Pkg, imgName)); err != nil {
			return fmt.Errorf("download file %s error: %w", f, err)
		}
	}
	return nil
}
