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
	"encoding/json"
	"fmt"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

type DailyBuildsQueryParam struct {
	ProjectName string `json:"projectName"`
	Branch      string `json:"branch"`
	Component   string `json:"component"`
	BuildStatus string `json:"buildStatus"`
	StartTime   string `json:"startTime"`
	EndTime     string `json:"endTime"`
	PageNum     int    `json:"pageNum"`
	PageSize    int    `json:"pageSize"`
}

type DailyBuildsResp struct {
	Result struct {
		DailyBuildVos []*DailyBuild `json:"dailyBuildVos"`
		Total         int           `json:"total"`
	} `json:"result"`
}

type DailyBuild struct {
	CurrentStatus   string `json:"currentStatus"`
	BuildStartTime  string `json:"buildStartTime"`
	BuildFailReason string `json:"buildFailReason"`
	Id              string `json:"id"`
	ObsPath         string `json:"obsPath"`
	ImgObsPath      string `json:"imgObsPath"`
}

func (m *Manager) loopCI(param DailyBuildsQueryParam, cur string, getFn func(cur string, resp *DailyBuild) string) string {
	for {
		file := func() string {
			data, err := json.Marshal(param)
			if err != nil {
				logrus.Errorf("can not marshal query param: %v", err)
				return ""
			}
			resp, err := utils.DoSimpleHttpReq(http.MethodPost, "http://ci.openharmony.cn/api/ci-backend/ci-portal/v1/dailybuilds", data, map[string]string{"Content-Type": "application/json;charset=UTF-8"})
			if err != nil {
				logrus.Errorf("can not query builds: %v", err)
				return ""
			}
			var dailyBuildsResp DailyBuildsResp
			if err := json.Unmarshal(resp, &dailyBuildsResp); err != nil {
				logrus.Errorf("can not unmarshal resp [%s]: %v", string(resp), err)
				return ""
			}
			if len(dailyBuildsResp.Result.DailyBuildVos) == 0 {
				return ""
			}
			if dailyBuildsResp.Result.DailyBuildVos[0].CurrentStatus != "end" {
				return ""
			}
			return getFn(cur, dailyBuildsResp.Result.DailyBuildVos[0])
		}()
		if file != "" {
			return file
		}
		time.Sleep(10 * time.Minute)
	}
}

func (m *Manager) getNewerFromCI(cur string) string {
	return m.loopCI(DailyBuildsQueryParam{
		ProjectName: "openharmony",
		Branch:      m.Branch,
		Component:   m.Component,
		BuildStatus: "success",
		PageNum:     1,
		PageSize:    1,
	}, cur, m.getNewerDailyBuild)
}

func (m *Manager) getNewerDailyBuild(cur string, db *DailyBuild) string {
	p := db.ImgObsPath
	if p == "" {
		p = db.ObsPath
	}
	if filepath.Base(p) == cur {
		return ""
	}
	logrus.Infof("new package found, name: %s", filepath.Base(p))
	file, err := m.downloadToWorkspace(p)
	if err != nil {
		logrus.Errorf("can not download package %s: %v", p, err)
		return ""
	}
	return file
}

func (m *Manager) downloadToWorkspace(url string) (string, error) {
	if _, err := parseTime(filepath.Base(url)); err != nil {
		logrus.Errorf("can not get package time from %s, skipping", filepath.Base(url))
		return "", fmt.Errorf("can not get package time from %s, skipping", filepath.Base(url))
	}
	logrus.Infof("downloading %s", url)
	resp, err := utils.DoSimpleHttpReqRaw(http.MethodGet, url, nil, nil)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if err := os.MkdirAll(m.ArchiveDir, 0750); err != nil {
		return "", err
	}
	f, err := os.Create(filepath.Join(m.ArchiveDir, filepath.Base(url)))
	if err != nil {
		return "", err
	}
	defer f.Close()
	if _, err := io.CopyBuffer(f, resp.Body, make([]byte, 16*1024*1024)); err != nil {
		return "", err
	}
	logrus.Infof("%s downloaded successfully", url)
	return filepath.Base(url), nil
}
