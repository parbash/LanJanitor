// Vue 3 app.js for LanJanitor

console.log('LanJanitor Vue.js app.js loaded');

const getCSRFToken = () => {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
};

const api = {
  getServers() {
    console.log('API: getServers called');
    return fetch('/api/servers').then(r => r.json());
  },
  addServer(name, ip, csrf) {
    console.log('API: addServer called', name, ip);
    return fetch('/api/servers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ name, ip })
    }).then(r => r.json());
  },
  delServer(id, csrf) {
    console.log('API: delServer called', id);
    return fetch(`/api/servers?id=${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': csrf }
    }).then(r => r.json());
  },
  rebootServer(ip, name, csrf) {
    console.log('API: rebootServer called', ip, name);
    return fetch('/api/reboot', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ ip, name })
    }).then(r => r.json());
  },
  upgradeServer(ip, csrf) {
    console.log('API: upgradeServer called', ip);
    return fetch(`/api/updates?ip=${encodeURIComponent(ip)}`, {
      method: 'GET',
      headers: { 'X-CSRFToken': csrf }
    }).then(r => r.json());
  },
  getKey() {
    console.log('API: getKey called');
    return fetch('/api/key').then(r => r.text());
  },
  changePassword(oldPassword, newPassword, csrf) {
    console.log('API: changePassword called');
    return fetch('/api/set_password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
    }).then(r => r.json());
  },
  logout(csrf) {
    console.log('API: logout called');
    return fetch('/api/logout', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf }
    });
  },
  login(username, password, csrf) {
    console.log('API: login called', username);
    return fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ username, password })
    });
  }
};

// Main app logic for index.html and settings.html
if (document.getElementById('app')) {
  const page = document.body.getAttribute('data-page');
  const csrf = getCSRFToken();

  console.log('Mounting Vue app to #app');

  const app = Vue.createApp({
    data() {
      return {
        servers: [],
        newServerName: '',
        newServerIP: '',
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
        loginError: ''
      };
    },
    mounted() {
      console.log('Vue app mounted and running!');
      console.log('Vue app mounted');
      if (window.location.pathname === '/' || window.location.pathname === '/settings') {
        this.fetchServers();
        this.fetchKey();
      }
    },
    methods: {
      fetchServers() {
        console.log('Method: fetchServers');
        api.getServers().then(data => { this.servers = data; });
      },
      addServer() {
        console.log('Method: addServer', this.newServerName, this.newServerIP);
        if (!this.newServerName || !this.newServerIP) return;
        api.addServer(this.newServerName, this.newServerIP, csrf).then(() => {
          this.newServerName = '';
          this.newServerIP = '';
          this.fetchServers();
        });
      },
      delServer(id, name) {
        console.log('Method: delServer', id, name);
        if (!confirm(`Delete ${name}?`)) return;
        api.delServer(id, csrf).then(() => this.fetchServers());
      },
      rebootServer(ip, name) {
        console.log('Method: rebootServer', ip, name);
        if (!confirm(`Reboot ${name}? This will restart the server.`)) return;
        this.showOverlay = true;
        api.rebootServer(ip, name, csrf).then(() => {
          setTimeout(() => {
            this.fetchServers();
            this.showOverlay = false;
          }, 10000);
        });
      },
      upgradeServer(ip, name) {
        console.log('Method: upgradeServer', ip, name);
        if (!confirm(`Install updates on ${name}?`)) return;
        this.showOverlay = true;
        api.upgradeServer(ip, csrf).then(() => {
          this.fetchServers();
          this.showOverlay = false;
        });
      },
      fetchKey() {
        console.log('Method: fetchKey');
        api.getKey().then(data => { this.publickey = data; });
      },
      changePassword() {
        console.log('Method: changePassword');
        if (this.newPassword !== this.confirmPassword) {
          this.passwordChangeError = 'Passwords do not match.';
          this.passwordChangeSuccess = false;
          return;
        }
        api.changePassword(this.currentPassword, this.newPassword, csrf).then(resp => {
          if (resp.status === 'ok') {
            this.passwordChangeSuccess = true;
            this.passwordChangeError = '';
            this.currentPassword = this.newPassword = this.confirmPassword = '';
          } else {
            this.passwordChangeSuccess = false;
            this.passwordChangeError = resp.error || 'Password change failed.';
          }
        });
      },
      logout() {
        console.log('Method: logout');
        api.logout(csrf).then(() => { window.location.href = '/login'; });
      },
      // For login page
      login() {
        console.log('Method: login', this.username);
        api.login(this.username, this.password, csrf).then(res => {
          console.log('Login response:', res);
          if (res.ok) {
            window.location.href = '/';
          } else {
            this.loginError = 'Invalid username or password';
            res.text().then(txt => console.log('Login error response body:', txt));
          }
        }).catch(err => {
          console.error('Login fetch error:', err);
          this.loginError = 'Login request failed.';
        });
      }
    }
  });
  app.config.compilerOptions.delimiters = ['[[', ']]'];
  app.mount('#app');
  console.log('Vue app mounted to #app');
}