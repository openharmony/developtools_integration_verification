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

package utils

import (
	"fmt"
	"github.com/sirupsen/logrus"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

type ProxyConfig struct {
	ServerList string `key:"server_list" default:""`
	User       string `key:"user" default:""`
	Password   string `key:"password" default:""`
}

var proxyClient = http.DefaultClient
var (
	proxyUser     string
	proxyPassword string
	proxyList     []string
	proxyIndex    int
	proxyLock     sync.Mutex
)

func init() {
	var config ProxyConfig
	ParseFromConfigFile("proxy", &config)
	if len(config.ServerList) != 0 {
		proxyList = strings.Split(config.ServerList, ",")
	}
	proxyUser = config.User
	proxyPassword = config.Password
	proxyIndex = len(proxyList)
	SwitchProxy()
	t := time.NewTicker(6 * time.Hour)
	go func() {
		<-t.C
		proxyLock.Lock()
		proxyIndex = len(proxyList)
		proxyLock.Unlock()
	}()
}

func SwitchProxy() {
	if len(proxyList) == 0 {
		return
	}
	proxyLock.Lock()
	defer proxyLock.Unlock()
	proxyIndex++
	if proxyIndex >= len(proxyList) {
		proxyIndex = 0
	}
	var proxyURL *url.URL
	var err error
	logrus.Infof("switching proxy to %s", proxyList[proxyIndex])
	if proxyUser == "" {
		proxyURL, err = url.Parse(fmt.Sprintf("http://%s", proxyList[proxyIndex]))
	} else {
		proxyURL, err = url.Parse(fmt.Sprintf("http://%s:%s@%s", proxyUser, url.QueryEscape(proxyPassword), proxyList[proxyIndex]))
	}
	if err != nil {
		logrus.Errorf("failed to parse proxy url, err: %v", err)
	}
	proxyClient = &http.Client{
		Transport: &http.Transport{
			Proxy: http.ProxyURL(proxyURL),
		},
	}
}
