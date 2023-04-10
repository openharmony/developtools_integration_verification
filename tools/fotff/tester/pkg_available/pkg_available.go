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

package pkg_available

import (
	"context"
	"fotff/tester"
	"github.com/sirupsen/logrus"
	"math/rand"
	"os"
	"strings"
	"sync"
	"time"
)

type Tester struct {
	device2PkgDir sync.Map
}

func init() {
	rand.Seed(time.Now().UnixNano())
}

func NewTester() tester.Tester {
	ret := &Tester{}
	return ret
}

func (t *Tester) TaskName() string {
	return "pkg_available"
}

func (t *Tester) Prepare(pkgDir string, device string, ctx context.Context) error {
	t.device2PkgDir.Store(device, pkgDir)
	return nil
}

func (t *Tester) DoTestTask(deviceSN string, ctx context.Context) (ret []tester.Result, err error) {
	return t.DoTestCases(deviceSN, []string{"pkg_available"}, ctx)
}

func (t *Tester) DoTestCase(deviceSN, testCase string, ctx context.Context) (ret tester.Result, err error) {
	pkgDir, _ := t.device2PkgDir.Load(deviceSN)
	es, err := os.ReadDir(pkgDir.(string))
	if err != nil {
		logrus.Errorf("can not read dir %s, testcase failed", pkgDir.(string))
		return tester.Result{TestCaseName: testCase, Status: tester.ResultFail}, nil
	}
	for _, e := range es {
		if strings.HasSuffix(e.Name(), ".img") {
			logrus.Infof("find image in dir %s, package is avaliable, testcase pass", pkgDir.(string))
			return tester.Result{TestCaseName: testCase, Status: tester.ResultPass}, nil
		}
	}
	logrus.Infof("no images in dir %s, package is not avaliable, testcase failed", pkgDir.(string))
	return tester.Result{TestCaseName: testCase, Status: tester.ResultFail}, nil
}

func (t *Tester) DoTestCases(deviceSN string, testcases []string, ctx context.Context) (ret []tester.Result, err error) {
	for _, testcase := range testcases {
		r, err := t.DoTestCase(deviceSN, testcase, ctx)
		if err != nil {
			return nil, err
		}
		ret = append(ret, r)
	}
	return ret, nil
}
