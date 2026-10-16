const { Plugin, Notice } = require('obsidian');

module.exports = class ArsArcanumPlugin extends Plugin {
  async onload() {
    console.log('Loading Ars Arcanum Studio Bridge plugin');

    // Status bar item
    this.statusBarItem = this.addStatusBarItem();
    this.statusBarItem.addClass('ars-arcanum-status-bar');
    this.updateStatusBar('⚡ Arcanum: Ready', 'pass');
    this.statusBarItem.onClickEvent(() => {
      window.open('http://127.0.0.1:4242', '_blank');
    });

    // Ribbon Icon
    this.addRibbonIcon('feather', 'Open Ars Arcanum Studio (127.0.0.1:4242)', () => {
      window.open('http://127.0.0.1:4242', '_blank');
      new Notice('Opened Ars Arcanum Studio Cockpit in browser');
    });

    // Commands
    this.addCommand({
      id: 'open-studio-cockpit',
      name: 'Open Visual Studio Cockpit (127.0.0.1:4242)',
      callback: () => {
        window.open('http://127.0.0.1:4242', '_blank');
      }
    });

    this.addCommand({
      id: 'check-continuity-diagnostics',
      name: 'Check Continuity Diagnostics & Update Status',
      callback: async () => {
        await this.pollDiagnostics();
      }
    });

    // Watch for _Arcanum_Diagnostics.md changes in vault
    this.registerEvent(
      this.app.vault.on('modify', (file) => {
        if (file.name === '_Arcanum_Diagnostics.md') {
          this.readDiagnosticsFile(file);
        }
      })
    );

    // Initial check
    this.pollDiagnostics();
    this.registerInterval(window.setInterval(() => this.pollDiagnostics(), 30000));
  }

  updateStatusBar(text, statusClass) {
    this.statusBarItem.setText(text);
    this.statusBarItem.removeClass('ars-arcanum-pass', 'ars-arcanum-warn', 'ars-arcanum-error');
    if (statusClass) {
      this.statusBarItem.addClass(`ars-arcanum-${statusClass}`);
    }
  }

  async readDiagnosticsFile(file) {
    try {
      const content = await this.app.vault.read(file);
      if (content.includes('status: PASS')) {
        this.updateStatusBar('✓ Arcanum: Clean', 'pass');
      } else {
        this.updateStatusBar('⚠️ Arcanum: Action Req', 'warn');
      }
    } catch (e) {
      this.updateStatusBar('⚡ Arcanum: Offline', '');
    }
  }

  async pollDiagnostics() {
    // Check if _Arcanum_Diagnostics.md exists in vault root
    const diagFile = this.app.vault.getAbstractFileByPath('_Arcanum_Diagnostics.md');
    if (diagFile) {
      await this.readDiagnosticsFile(diagFile);
      return;
    }

    // Otherwise check local daemon API
    try {
      const res = await fetch('http://127.0.0.1:4242/api/status');
      if (res.ok) {
        this.updateStatusBar('⚡ Arcanum: Connected', 'pass');
      } else {
        this.updateStatusBar('⚡ Arcanum: Ready', '');
      }
    } catch (e) {
      this.updateStatusBar('⚡ Arcanum: Standby', '');
    }
  }

  onunload() {
    console.log('Unloading Ars Arcanum Studio Bridge plugin');
  }
};
