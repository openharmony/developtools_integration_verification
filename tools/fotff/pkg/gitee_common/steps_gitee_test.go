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
	"fotff/vcs"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestMain(m *testing.M) {
	defer os.RemoveAll(".fotff")
	defer os.RemoveAll("logs")
	m.Run()
}

func TestManager_Steps(t *testing.T) {
	m := &Manager{Workspace: "./testdata", Branch: "master"}
	defer func() {
		entries, _ := os.ReadDir(m.Workspace)
		for _, e := range entries {
			if strings.HasPrefix(e.Name(), "version") {
				continue
			}
			os.RemoveAll(filepath.Join(m.Workspace, e.Name()))
		}
	}()
	tests := []struct {
		name     string
		from, to string
		stepsNum int
	}{
		{
			name:     "15 MR of 15 steps in 12 repo, with 1 path change",
			from:     "version-Daily_Version-dayu200-20221201_080109-dayu200",
			to:       "version-Daily_Version-dayu200-20221201_100141-dayu200",
			stepsNum: 15,
		},
		{
			name:     "27 MR of 25 steps in 21 repo, with 1 repo add",
			from:     "version-Daily_Version-dayu200-20221213_110027-dayu200",
			to:       "version-Daily_Version-dayu200-20221213_140150-dayu200",
			stepsNum: 25,
		},
		{
			name:     "15 MR of 14 steps in 14 repo, no structure change",
			from:     "version-Daily_Version-dayu200-20221214_100124-dayu200",
			to:       "version-Daily_Version-dayu200-20221214_110125-dayu200",
			stepsNum: 14,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ret, err := m.Steps(tt.from, tt.to)
			if err != nil {
				t.Fatalf("err: expcect: <nil>, actual: %v", err)
			}
			if len(ret) != tt.stepsNum {
				t.Fatalf("steps num: expcect: %d, actual: %v", tt.stepsNum, len(ret))
			}
			if tt.stepsNum == 0 {
				return
			}
			mLast, err := vcs.ParseManifestFile(filepath.Join(m.Workspace, ret[len(ret)-1], "manifest_tag.xml"))
			if err != nil {
				t.Fatalf("err: expcect: <nil>, actual: %v", err)
			}
			mLastMD5, err := mLast.Standardize()
			if err != nil {
				t.Fatalf("err: expcect: <nil>, actual: %v", err)
			}
			expected, err := vcs.ParseManifestFile(filepath.Join(m.Workspace, tt.to, "manifest_tag.xml"))
			if err != nil {
				t.Fatalf("err: expcect: <nil>, actual: %v", err)
			}
			expectedMD5, err := expected.Standardize()
			if err != nil {
				t.Fatalf("err: expcect: <nil>, actual: %v", err)
			}
			if mLastMD5 != expectedMD5 {
				t.Errorf("steps result: expect: %s, actual: %s", expectedMD5, mLastMD5)
			}
		})
	}
}
