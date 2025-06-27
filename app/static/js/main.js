// Main entry for LanJanitor Vue app
// Assumes api.js, utils.js, and all components are loaded before this file

console.log('LanJanitor main.js loaded');

if (typeof Vue === 'undefined') {
  console.error('Vue is not loaded!');
}
if (!window.ServerCard || !window.AddServerModal || !window.LoadingOverlay || !window.NavbarBar || !window.FooterBar) {
  console.error('One or more Vue components are not loaded!');
}

if (document.getElementById('app')) {
  const page = document.body.getAttribute('data-page');
  const csrf = getCSRFToken();
  console.log('Mounting Vue app to #app');

  // Use custom delimiters to avoid Jinja conflict
  const delimiters = window.LANJANITOR_VUE_DELIMITERS || ['[[', ']]'];
  const app = Vue.createApp({
    data() {
      return {
        servers: [],
        newServerName: '',
        newServerIP: '',
        newServerOsType: 'Ubuntu',
        showOverlay: false,
        publickey: '',
        // For settings page
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        passwordChangeSuccess: false,
        passwordChangeError: '',
        // For login page
        username: '',
        password: '',
        loginError: '',
        checkAllUpdatesMsg: '',
        checkingAllUpdates: false,
        toastMsg: '',
        toastType: 'info',
        showToast: false,
        darkMode: false
      };
    },
    mounted() {
      if (window.location.pathname === '/' || window.location.pathname === '/settings') {
        this.fetchServers();
        this.fetchKey();
      }
      // Inject toast container if not present
      if (!document.getElementById('toast-container')) {
        const toastDiv = document.createElement('div');
        toastDiv.id = 'toast-container';
        toastDiv.style.position = 'fixed';
        toastDiv.style.top = '1.5rem';
        toastDiv.style.right = '1.5rem';
        toastDiv.style.zIndex = '2000';
        document.body.appendChild(toastDiv);
      }
      // Dark mode: check localStorage and set initial state
      if (localStorage.getItem('lanjanitor-darkmode') === 'true') {
        this.darkMode = true;
        document.body.classList.add('dark-mode');
      }
    },
    components: {
      'server-card': window.ServerCard,
      'add-server-modal': window.AddServerModal,
      'loading-overlay': window.LoadingOverlay,
      'navbar-bar': window.NavbarBar,
      'footer-bar': window.FooterBar
    },
    methods: {
      async fetchServers() {
        try {
          this.servers = await api.getServers();
        } catch (err) {
          this.servers = [];
          alert('Failed to fetch servers.');
        }
      },
      async addServer() {
        if (!this.newServerName || !this.newServerIP) return;
        try {
          await api.addServer(this.newServerName, this.newServerIP, this.newServerOsType, csrf);
          this.newServerName = '';
          this.newServerIP = '';
          this.newServerOsType = 'Ubuntu';
          await this.fetchServers();
        } catch (err) {
          alert('Failed to add server.');
        }
      },
      async delServer(id, name) {
        if (!confirm(`Delete ${name}?`)) return;
        try {
          await api.delServer(id, csrf);
          await this.fetchServers();
        } catch (err) {
          alert('Failed to delete server.');
        }
      },
      async rebootServer(ip, name) {
        if (!confirm(`Reboot ${name}? This will restart the server.`)) return;
        this.showOverlay = true;
        try {
          await api.rebootServer(ip, name, csrf);
          setTimeout(async () => {
            await this.fetchServers();
            this.showOverlay = false;
          }, 10000);
        } catch (err) {
          this.showOverlay = false;
          alert('Failed to reboot server.');
        }
      },
      async upgradeServer(ip, name) {
        if (!confirm(`Install updates on ${name}?`)) return;
        this.showOverlay = true;
        try {
          await api.upgradeServer(ip, csrf);
          await this.fetchServers();
          this.showOverlay = false;
        } catch (err) {
          this.showOverlay = false;
          alert('Failed to upgrade server.');
        }
      },
      async fetchKey() {
        try {
          this.publickey = await api.getKey();
        } catch (err) {
          this.publickey = '';
          alert('Failed to fetch SSH key.');
        }
      },
      async changePassword() {
        if (this.newPassword !== this.confirmPassword) {
          this.passwordChangeError = 'Passwords do not match.';
          this.passwordChangeSuccess = false;
          return;
        }
        try {
          const resp = await api.changePassword(this.currentPassword, this.newPassword, csrf);
          if (resp.status === 'ok') {
            this.passwordChangeSuccess = true;
            this.passwordChangeError = '';
            this.currentPassword = this.newPassword = this.confirmPassword = '';
          } else {
            this.passwordChangeSuccess = false;
            this.passwordChangeError = resp.error || 'Password change failed.';
          }
        } catch (err) {
          this.passwordChangeSuccess = false;
          this.passwordChangeError = 'Password change failed.';
        }
      },
      async logout() {
        try {
          await api.logout(csrf);
        } catch (err) {}
        window.location.href = '/login';
      },
      async login() {
        try {
          const res = await api.login(this.username, this.password, csrf);
          if (res.ok) {
            window.location.href = '/';
          } else {
            this.loginError = 'Invalid username or password';
            res.text().then(txt => console.log('Login error response body:', txt));
          }
        } catch (err) {
          this.loginError = 'Login request failed.';
        }
      },
      showPopup(msg, type = 'info') {
        this.toastMsg = msg;
        this.toastType = type;
        this.showToast = true;
        // Create toast markup
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
          <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0 show" role="alert" aria-live="assertive" aria-atomic="true" style="min-width: 250px;">
            <div class="d-flex">
              <div class="toast-body">${msg}</div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
          </div>`;
        const container = document.getElementById('toast-container');
        container.insertAdjacentHTML('beforeend', toastHtml);
        const toastElem = document.getElementById(toastId);
        const toast = bootstrap.Toast.getOrCreateInstance(toastElem, { delay: 3500 });
        toast.show();
        toastElem.addEventListener('hidden.bs.toast', () => toastElem.remove());
      },
      async checkAllUpdates() {
        this.checkingAllUpdates = true;
        this.checkAllUpdatesMsg = '';
        this.showPopup('Update check started on all servers.', 'info');
        try {
          const res = await fetch('/api/updates/all', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCSRFToken() }
          });
          if (res.ok) {
            const data = await res.json();
            this.checkAllUpdatesMsg = data.message || 'Update check triggered on all servers.';
            this.showPopup(data.message || 'Update check completed.', 'success');
            await this.fetchServers();
          } else {
            this.checkAllUpdatesMsg = 'Failed to trigger update check.';
            this.showPopup('Failed to trigger update check.', 'danger');
          }
        } catch (err) {
          this.checkAllUpdatesMsg = 'Error contacting server.';
          this.showPopup('Error contacting server.', 'danger');
        } finally {
          this.checkingAllUpdates = false;
        }
      },
      toggleDarkMode() {
        // Only update body class and localStorage, do not flip darkMode here
        if (this.darkMode) {
          document.body.classList.add('dark-mode');
          localStorage.setItem('lanjanitor-darkmode', 'true');
        } else {
          document.body.classList.remove('dark-mode');
          localStorage.setItem('lanjanitor-darkmode', 'false');
        }
      }
    }
  });
  app.config.compilerOptions.delimiters = delimiters;
  app.mount('#app');
  console.log('Vue app mounted to #app');
}
