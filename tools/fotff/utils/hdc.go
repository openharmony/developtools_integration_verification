package utils

import (
	"context"
	"errors"
	"github.com/sirupsen/logrus"
	"os/exec"
	"strings"
	"time"
)

var hdc string

func init() {
	if hdc, _ = exec.LookPath("hdc"); hdc == "" {
		hdc, _ = exec.LookPath("hdc_std")
	}
	if hdc == "" {
		logrus.Panicf("can not find 'hdc', please install")
	}
}

func WaitHDC(device string, ctx context.Context) bool {
	ctx, cancelFn := context.WithTimeout(ctx, 20*time.Second)
	defer cancelFn()
	for {
		select {
		case <-ctx.Done():
			return false
		default:
		}
		ExecContext(ctx, hdc, "kill")
		time.Sleep(time.Second)
		ExecContext(ctx, hdc, "start")
		time.Sleep(time.Second)
		out, err := ExecCombinedOutputContext(ctx, hdc, "list", "targets")
		if err != nil {
			if errors.Is(err, context.Canceled) {
				return false
			}
			logrus.Errorf("failed to list hdc targets: %s, %s", string(out), err)
			continue
		}
		lines := strings.Fields(string(out))
		for _, dev := range lines {
			if dev == "[Empty]" {
				logrus.Warn("can not find any hdc targets")
				break
			}
			if device == "" || dev == device {
				return true
			}
		}
		logrus.Infof("%s not found", device)
	}
}

func TryRebootToLoader(device string, ctx context.Context) error {
	logrus.Infof("try to reboot %s to loader...", device)
	defer time.Sleep(5 * time.Second)
	if connected := WaitHDC(device, ctx); connected {
		if device == "" {
			return ExecContext(ctx, hdc, "shell", "reboot", "loader")
		} else {
			return ExecContext(ctx, hdc, "-t", device, "shell", "reboot", "loader")
		}
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	logrus.Warn("can not find target hdc device, assume it has been in loader mode")
	return nil
}

func HdcShell(cmd, device string, ctx context.Context) error {
	if device == "" {
		return ExecContext(ctx, hdc, "shell", cmd)
	} else {
		return ExecContext(ctx, hdc, "-t", device, "shell", cmd)
	}
}
