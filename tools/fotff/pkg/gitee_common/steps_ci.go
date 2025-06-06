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
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"time"
)

type TagQueryParam struct {
	ProjectName  string `json:"projectName"`
	Branch       string `json:"branch"`
	ManifestFile string `json:"manifestFile"`
	StartTime    string `json:"startTime"`
	EndTime      string `json:"endTime"`
	PageNum      int    `json:"pageNum"`
	PageSize     int    `json:"pageSize"`
}

type TagResp struct {
	Result struct {
		TagList []*Tag `json:"tagList"`
		Total   int    `json:"total"`
	} `json:"result"`
}

type Tag struct {
	Id         string   `json:"id"`
	Issue      string   `json:"issue"`
	PrList     []string `json:"prList"`
	TagFileURL string   `json:"tagFileUrl"`
	Timestamp  string   `json:"timestamp"`
}

func (m *Manager) stepsFromCI(from, to string) (pkgs []string, err error) {
	startTime, err := parseTime(from)
	if err != nil {
		return nil, err
	}
	endTime, err := parseTime(to)
	if err != nil {
		return nil, err
	}
	return m.getAllStepsFromTags(startTime, endTime)
}

func (m *Manager) getAllStepsFromTags(from, to time.Time) (pkgs []string, err error) {
	tags, err := m.getAllTags(from, to)
	if err != nil {
		return nil, err
	}
	for _, tag := range tags {
		pkg, err := m.genTagPackage(tag)
		if err != nil {
			return nil, err
		}
		pkgs = append(pkgs, pkg)
	}
	return pkgs, nil
}

func (m *Manager) getAllTags(from, to time.Time) (ret []*Tag, err error) {
	var deDup = make(map[string]*Tag)
	var pageNum = 1
	for {
		var q = TagQueryParam{
			ProjectName:  "openharmony",
			Branch:       m.ManifestBranch,
			ManifestFile: "default.xml",
			StartTime:    from.Local().Format("2006-01-02"),
			EndTime:      to.Local().Format("2006-01-02"),
			PageNum:      pageNum,
			PageSize:     10000,
		}
		data, err := json.Marshal(q)
		if err != nil {
			return nil, err
		}
		resp, err := utils.DoSimpleHttpReq(http.MethodPost, "http://ci.openharmony.cn/api/ci-backend/ci-portal/v1/build/tag", data, map[string]string{"Content-Type": "application/json;charset=UTF-8"})
		if err != nil {
			return nil, err
		}
		var tagResp TagResp
		if err := json.Unmarshal(resp, &tagResp); err != nil {
			return nil, err
		}
		for _, tag := range tagResp.Result.TagList {
			if _, ok := deDup[tag.Id]; ok {
				continue
			}
			deDup[tag.Id] = tag
			date, err := time.ParseInLocation("2006-01-02 15:04:05", tag.Timestamp, time.Local)
			if err != nil {
				return nil, err
			}
			if date.After(from) && date.Before(to) {
				ret = append(ret, tag)
			}
		}
		if len(deDup) == tagResp.Result.Total {
			break
		}
		pageNum++
	}
	sort.Slice(ret, func(i, j int) bool {
		return ret[i].Timestamp < ret[j].Timestamp
	})
	return ret, nil
}

func (m *Manager) genTagPackage(tag *Tag) (pkg string, err error) {
	defer func() {
		logrus.Infof("package dir %s for tag %v generated", pkg, tag.TagFileURL)
	}()
	if err := os.MkdirAll(filepath.Join(m.Workspace, tag.Id), 0750); err != nil {
		return "", err
	}
	var issues []string
	if len(tag.Issue) == 0 {
		issues = tag.PrList
	} else {
		issues = []string{tag.Issue}
	}
	if err := os.WriteFile(filepath.Join(m.Workspace, tag.Id, "__last_issue__"), []byte(fmt.Sprintf("%v", issues)), 0640); err != nil {
		return "", err
	}
	resp, err := utils.DoSimpleHttpReq(http.MethodGet, tag.TagFileURL, nil, nil)
	if err != nil {
		return "", err
	}
	err = os.WriteFile(filepath.Join(m.Workspace, tag.Id, "manifest_tag.xml"), resp, 0640)
	if err != nil {
		return "", err
	}
	return tag.Id, nil
}
