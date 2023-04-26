/*
 * Copyright (c) 2022-2023 Huawei Device Co., Ltd.
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
	"fotff/pkg"
	"fotff/pkg/gitee_common"
	"fotff/res"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"strconv"
	"strings"
)

type Manager struct {
	ArchiveDir     string `key:"archive_dir" default:"archive"`
	WatchCI        string `key:"watch_ci" default:"false"`
	Workspace      string `key:"workspace" default:"workspace"`
	Branch         string `key:"branch" default:"master"`
	ManifestBranch string `key:"manifest_branch" default:"master"`
	FlashTool      string `key:"flash_tool" default:"python"`
	LocationIDList string `key:"location_id_list"`

	*gitee_common.Manager
	locations map[string]string
}

// These commands are copied from ci project.
const (
	preCompileCMD = `rm -rf prebuilts/clang/ohos/darwin-x86_64/clang-480513;rm -rf prebuilts/clang/ohos/windows-x86_64/clang-480513;rm -rf prebuilts/clang/ohos/linux-x86_64/clang-480513;bash build/prebuilts_download.sh`
	// compileCMD is copied from ci project and trim useless build-target 'make_test' to enhance build efficiency.
	compileCMD = `echo 'start' && export NO_DEVTOOL=1 && export CCACHE_LOG_SUFFIX="dayu200-arm32" && export CCACHE_NOHASHDIR="true" && export CCACHE_SLOPPINESS="include_file_ctime" && ./build.sh --product-name rk3568 --ccache --build-target make_all --gn-args enable_notice_collection=false`
)

// This list is copied from ci project. Some of them are not available, has been annotated.
var imgList = []string{
	"out/rk3568/packages/phone/images/MiniLoaderAll.bin",
	"out/rk3568/packages/phone/images/boot_linux.img",
	"out/rk3568/packages/phone/images/parameter.txt",
	"out/rk3568/packages/phone/images/system.img",
	"out/rk3568/packages/phone/images/uboot.img",
	"out/rk3568/packages/phone/images/userdata.img",
	"out/rk3568/packages/phone/images/vendor.img",
	"out/rk3568/packages/phone/images/resource.img",
	"out/rk3568/packages/phone/images/config.cfg",
	"out/rk3568/packages/phone/images/ramdisk.img",
	// "out/rk3568/packages/phone/images/chipset.img",
	"out/rk3568/packages/phone/images/sys_prod.img",
	"out/rk3568/packages/phone/images/chip_prod.img",
	"out/rk3568/packages/phone/images/updater.img",
	// "out/rk3568/packages/phone/updater/bin/updater_binary",
}

func NewManager() pkg.Manager {
	var ret Manager
	utils.ParseFromConfigFile("dayu200", &ret)
	watchCI, err := strconv.ParseBool(ret.WatchCI)
	if err != nil {
		logrus.Panicf("can not parse 'watch_ci', please check")
	}
	ret.Manager = gitee_common.NewManager("dayu200", ret.Branch, ret.ManifestBranch, ret.ArchiveDir, ret.Workspace, watchCI)
	devs := res.DeviceList()
	locs := strings.Split(ret.LocationIDList, ",")
	if len(devs) != len(locs) {
		logrus.Panicf("location_id_list and devices mismatch")
	}
	ret.locations = map[string]string{}
	for i, loc := range locs {
		ret.locations[devs[i]] = loc
	}
	return &ret
}

// Flash function implements pkg.Manager. Flash images in the 'pkg' directory to the given device.
// If not all necessary images are available in the 'pkg' directory, will build them.
func (m *Manager) Flash(device string, pkg string, ctx context.Context) error {
	logrus.Infof("now flash %s", pkg)
	buildConfig := gitee_common.BuildConfig{
		Pkg:           pkg,
		PreCompileCMD: preCompileCMD,
		CompileCMD:    compileCMD,
		ImgList:       imgList,
	}
	if err := m.Build(buildConfig, ctx); err != nil {
		logrus.Errorf("build %s fail, err: %v", pkg, err)
		return err
	}
	logrus.Infof("%s is available now, start to flash it", pkg)
	return m.flashDevice(device, pkg, ctx)
}
