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
	"context"
	"errors"
	"fmt"
	"github.com/pkg/sftp"
	"github.com/sirupsen/logrus"
	"golang.org/x/crypto/ssh"
	"io"
	"os"
	"path/filepath"
	"time"
)

func newSSHClient(addr string, user string, passwd string) (*ssh.Client, error) {
	config := &ssh.ClientConfig{
		User:            user,
		Auth:            []ssh.AuthMethod{ssh.Password(passwd)},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
	}
	config.SetDefaults()
	return ssh.Dial("tcp", addr, config)
}

func RunCmdViaSSHContext(ctx context.Context, addr string, user string, passwd string, cmd string) (err error) {
	ctx, fn := context.WithTimeout(ctx, 6*time.Hour)
	defer fn()
	if err := RunCmdViaSSHContextNoRetry(ctx, addr, user, passwd, cmd); err != nil {
		if errors.Is(err, context.Canceled) {
			return err
		}
		logrus.Errorf("exec cmd via SSH at %s failed: %v, try again...", addr, err)
		return RunCmdViaSSHContextNoRetry(ctx, addr, user, passwd, cmd)
	}
	return nil
}

func RunCmdViaSSHContextNoRetry(ctx context.Context, addr string, user string, passwd string, cmd string) (err error) {
	exit := make(chan struct{})
	client, err := newSSHClient(addr, user, passwd)
	if err != nil {
		logrus.Errorf("new SSH client to %s err: %v", addr, err)
		return err
	}
	defer client.Close()
	session, err := client.NewSession()
	if err != nil {
		return err
	}
	defer func() {
		select {
		case <-ctx.Done():
			err = ctx.Err()
		default:
		}
	}()
	defer close(exit)
	go func() {
		select {
		case <-ctx.Done():
		case <-exit:
		}
		session.Close()
	}()
	logrus.Infof("run at %s: %s", addr, cmd)
	stdin, err := session.StdinPipe()
	if err != nil {
		return err
	}
	defer stdin.Close()
	stdout, err := session.StdoutPipe()
	if err != nil {
		return err
	}
	stderr, err := session.StderrPipe()
	if err != nil {
		return err
	}
	if err := session.Shell(); err != nil {
		return err
	}
	cmd = fmt.Sprintf("%s\nexit $?\n", cmd)
	go stdin.Write([]byte(cmd))
	go io.Copy(os.Stdout, stdout)
	go io.Copy(os.Stderr, stderr)
	fmt.Printf("[%s] exec at %s %s :\n", time.Now(), addr, cmd)
	return session.Wait()
}

type Direct string

const (
	Download Direct = "download"
	Upload   Direct = "upload"
)

func TransFileViaSSH(verb Direct, addr string, user string, passwd string, remoteFile string, localFile string) error {
	c, err := newSSHClient(addr, user, passwd)
	if err != nil {
		logrus.Errorf("new SSH client to %s err: %v", addr, err)
		return err
	}
	defer c.Close()
	client, err := sftp.NewClient(c)
	if err != nil {
		logrus.Errorf("new SFTP client to %s err: %v", addr, err)
		return err
	}
	defer client.Close()
	var prep string
	var src, dst io.ReadWriteCloser
	if verb == Download {
		prep = "to"
		if src, err = client.Open(remoteFile); err != nil {
			return fmt.Errorf("open remote file %s at %s err: %v", remoteFile, addr, err)
		}
		defer src.Close()
		os.RemoveAll(localFile)
		os.MkdirAll(filepath.Dir(localFile), 0755)
		if dst, err = os.Create(localFile); err != nil {
			return fmt.Errorf("create local file err: %v", err)
		}
		defer dst.Close()
	} else {
		prep = "from"
		if src, err = os.Open(localFile); err != nil {
			return fmt.Errorf("open local file err: %v", err)
		}
		defer src.Close()
		client.Remove(remoteFile)
		client.MkdirAll(filepath.Dir(remoteFile))
		if dst, err = client.Create(remoteFile); err != nil {
			return fmt.Errorf("create remote file %s at %s err: %v", remoteFile, addr, err)
		}
		defer dst.Close()
	}
	logrus.Infof("%sing %s at %s %s %s...", verb, remoteFile, addr, prep, localFile)
	t1 := time.Now()
	n, err := io.CopyBuffer(dst, src, make([]byte, 32*1024*1024))
	if err != nil {
		logrus.Errorf("%s %s at %s %s %s err: %v", verb, remoteFile, addr, prep, localFile, err)
		return err
	}
	t2 := time.Now()
	cost := t2.Sub(t1).Seconds()
	logrus.Infof("%s %s at %s %s %s done, size: %d cost: %.2fs speed: %.2fMB/s", verb, remoteFile, addr, prep, localFile, n, cost, float64(n)/cost/1024/1024)
	return nil
}
