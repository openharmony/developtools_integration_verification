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
	"code.cloudfoundry.org/archiver/extractor"
	"context"
	"fmt"
	"fotff/utils"
	"github.com/sirupsen/logrus"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type Manager struct {
	Component  string
	Branch     string
	ArchiveDir string
	Workspace  string
	WatchCI    bool
}

func NewManager(component string, branch string, archiveDir string, workspace string, watchCI bool) *Manager {
	var ret = Manager{
		Component:  component,
		Branch:     branch,
		ArchiveDir: archiveDir,
		Workspace:  workspace,
		WatchCI:    watchCI,
	}
	go ret.cleanupOutdated()
	return &ret
}

func (m *Manager) cleanupOutdated() {
	t := time.NewTicker(24 * time.Hour)
	for {
		<-t.C
		es, err := os.ReadDir(m.Workspace)
		if err != nil {
			logrus.Errorf("can not read %s: %v", m.Workspace, err)
			continue
		}
		for _, e := range es {
			if !e.IsDir() {
				continue
			}
			path := filepath.Join(m.Workspace, e.Name())
			info, err := e.Info()
			if err != nil {
				logrus.Errorf("can not read %s info: %v", path, err)
				continue
			}
			if time.Now().Sub(info.ModTime()) > 7*24*time.Hour {
				logrus.Warnf("%s outdated, cleanning up its contents...", path)
				m.cleanupPkgFiles(path)
			}
		}
	}
}

func (m *Manager) cleanupPkgFiles(path string) {
	es, err := os.ReadDir(path)
	if err != nil {
		logrus.Errorf("can not read %s: %v", path, err)
		return
	}
	for _, e := range es {
		if e.Name() == "manifest_tag.xml" || e.Name() == "__last_issue__" {
			continue
		}
		if err := os.RemoveAll(filepath.Join(path, e.Name())); err != nil {
			logrus.Errorf("remove %s fail: %v", filepath.Join(path, e.Name()), err)
		}
	}
}

// Flash function implements pkg.Manager. Flash images in the 'pkg' directory to the given device.
func (m *Manager) Flash(device string, pkg string, ctx context.Context) error {
	logrus.Warnf("not implemented yet")
	return nil
}

func (m *Manager) Steps(from, to string) (pkgs []string, err error) {
	if from == to {
		return nil, fmt.Errorf("steps err: 'from' %s and 'to' %s are the same", from, to)
	}
	if c, found := utils.CacheGet(fmt.Sprintf("%s_steps", m.Component), from+"__to__"+to); found {
		logrus.Infof("steps from %s to %s are cached", from, to)
		logrus.Infof("steps: %v", c.([]string))
		return c.([]string), nil
	}
	if pkgs, err = m.stepsFromGitee(from, to); err != nil {
		logrus.Errorf("failed to gen steps from gitee, err: %v", err)
		logrus.Warnf("fallback to getting steps from CI...")
		if pkgs, err = m.stepsFromCI(from, to); err != nil {
			return pkgs, err
		}
		return pkgs, nil
	}
	utils.CacheSet(fmt.Sprintf("%s_steps", m.Component), from+"__to__"+to, pkgs)
	return pkgs, nil
}

func (m *Manager) LastIssue(pkg string) (string, error) {
	data, err := os.ReadFile(filepath.Join(m.Workspace, pkg, "__last_issue__"))
	return string(data), err
}

func (m *Manager) GetNewer(cur string) (string, error) {
	var newFile string
	if m.WatchCI {
		newFile = m.getNewerFromCI(cur + ".tar.gz")
	} else {
		newFile = m.getNewerFileFromDir(cur+".tar.gz", func(files []os.DirEntry, i, j int) bool {
			ti, _ := parseTime(files[i].Name())
			tj, _ := parseTime(files[j].Name())
			return ti.Before(tj)
		})
	}
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

func (m *Manager) PkgDir(pkg string) string {
	return filepath.Join(m.Workspace, pkg)
}
