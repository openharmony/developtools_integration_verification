/*
 * Copyright (c) 2023 Huawei Device Co., Ltd.
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

package gitee_build

import (
	"context"
	"fotff/pkg"
	"fotff/pkg/gitee_common"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"strings"
)

type Manager struct {
	ArchiveDir     string   `key:"archive_dir" default:"archive"`
	Workspace      string   `key:"workspace" default:"workspace"`
	Branch         string   `key:"branch" default:"master"`
	ManifestBranch string   `key:"manifest_branch" default:"master"`
	Component      string   `key:"component"`
	PreCompileCMD  string   `key:"pre_compile_cmd"`
	CompileCMD     string   `key:"compile_cmd"`
	ImageList      []string `key:"image_list"`

	*gitee_common.Manager
}

func NewManager() pkg.Manager {
	var ret Manager
	utils.ParseFromConfigFile("gitee_build", &ret)
	ret.Manager = gitee_common.NewManager(ret.Component, ret.Branch, ret.ManifestBranch, ret.ArchiveDir, ret.Workspace, true)
	return &ret
}

func (m *Manager) GetNewer(cur string) (string, error) {
	return m.GetNewerOrFail(cur)
}

// Flash function implements pkg.Manager. Since this gitee_build just tests package buildings,
// there is no need to flash images actually, just build it and return nil unconditionally.
func (m *Manager) Flash(device string, pkg string, ctx context.Context) error {
	logrus.Infof("now flash %s", pkg)
	buildConfig := gitee_common.BuildConfig{
		Pkg:           pkg,
		PreCompileCMD: m.PreCompileCMD,
		CompileCMD:    m.CompileCMD,
		ImgList:       m.ImageList,
	}
	if m.PkgAvailable(buildConfig) {
		return nil
	}
	if strings.Contains(buildConfig.Pkg, "build_fail") {
		logrus.Warnf("here is a known build_fail token package")
	} else {
		if err := m.BuildNoRetry(buildConfig, true, ctx); err != nil {
			logrus.Warnf("build %s fail, err: %v", pkg, err)
		} else {
			logrus.Infof("%s is available now", pkg)
		}
	}
	logrus.Infof("since fotff just tests package buildings, there is no need to flash images actually, mark flash as a success unconditionally")
	return nil
}
