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

package gitee_common

import (
	"code.cloudfoundry.org/archiver/compressor"
	"code.cloudfoundry.org/archiver/extractor"
	"fmt"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

func (m *Manager) GetNewerOrFail(cur string) (string, error) {
	newFile := m.getNewerOrFailFromCI(cur + ".tar.gz")
	ex := extractor.NewTgz()
	dirName := strings.TrimSuffix(newFile, ".tar.gz")
	dir := filepath.Join(m.Workspace, dirName)
	if _, err := os.Stat(dir); err == nil {
		return dirName, nil
	}
	logrus.Infof("extracting %s to %s...", filepath.Join(m.ArchiveDir, newFile), dir)
	if err := ex.Extract(filepath.Join(m.ArchiveDir, newFile), dir); err != nil {
		return dirName, err
	}
	return dirName, nil
}

func (m *Manager) getNewerOrFailFromCI(cur string) string {
	return m.loopCI(DailyBuildsQueryParam{
		ProjectName: "openharmony",
		Branch:      m.Branch,
		Component:   m.Component,
		PageNum:     1,
		PageSize:    1,
	}, cur, m.getNewerDailyBuildOrFail)
}

func (m *Manager) getNewerDailyBuildOrFail(cur string, db *DailyBuild) string {
	switch db.BuildFailReason {
	case "":
		return m.getNewerDailyBuild(cur, db)
	case "compile_failed":
		lastSuccessTime, err := parseTime(cur)
		if err != nil {
			logrus.Errorf("can not get package time from %s, skipping", cur)
			return ""
		}
		nowFailTime, err := parseTime(db.BuildStartTime)
		if err != nil {
			logrus.Errorf("can not get time from %s, skipping", cur)
			return ""
		}
		if lastSuccessTime == nowFailTime {
			return ""
		}
		return m.genFailedPackage(lastSuccessTime, nowFailTime)
	default:
		return ""
	}
}

func (m *Manager) genFailedPackage(lastSuccessTime, failedBuildStartTime time.Time) string {
	pkg := fmt.Sprintf("%s_%s_build_fail", m.Component, failedBuildStartTime.Format("20060102_150405"))
	logrus.Infof("getting failed package manifest for %s(%s) at %s", m.Component, m.Branch, failedBuildStartTime)
	tags, err := m.getAllTags(lastSuccessTime, failedBuildStartTime)
	if err != nil {
		logrus.Errorf("can not get latest tag from ci, err: %v", err)
		return ""
	}
	if len(tags) == 0 {
		logrus.Error("can not get latest tag from ci, tag list is empty")
		return ""
	}
	if err := os.MkdirAll(filepath.Join(m.Workspace, pkg), 0750); err != nil {
		logrus.Errorf("can not mkdir %s, err: %v", pkg, err)
		return ""
	}
	resp, err := utils.DoSimpleHttpReq(http.MethodGet, tags[len(tags)-1].TagFileURL, nil, nil)
	if err != nil {
		logrus.Errorf("can not get latest tag file from ci, err: %v", err)
		return ""
	}
	err = os.WriteFile(filepath.Join(m.Workspace, pkg, "manifest_tag.xml"), resp, 0640)
	if err != nil {
		logrus.Errorf("can not write latest tag file, err: %v", err)
		return ""
	}
	if err := compressor.NewTgz().Compress(filepath.Join(m.Workspace, pkg), filepath.Join(m.ArchiveDir, pkg+".tar.gz")); err != nil {
		logrus.Errorf("can not write latest tag file, err: %v", err)
		return ""
	}
	return pkg + ".tar.gz"
}
