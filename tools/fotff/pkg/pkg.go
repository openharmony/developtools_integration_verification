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

package pkg

import (
	"context"
)

type NewFunc func() Manager

type Manager interface {
	// Flash download given package to the device.
	Flash(device string, pkg string, ctx context.Context) error
	// LastIssue returns the last issue URL related to the package.
	LastIssue(pkg string) (string, error)
	// Steps generates every intermediate package and returns the list sequentially.
	Steps(from, to string) ([]string, error)
	// GetNewer blocks the process until a newer package is found, then returns the newest one.
	GetNewer(cur string) (string, error)
	// PkgDir returns where pkg exists in the filesystem.
	PkgDir(pkg string) string
}
