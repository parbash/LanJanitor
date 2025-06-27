// API functions for LanJanitor
const api = {
  getServers() {
    return fetch('/api/servers')
      .then(r => r.ok ? r.json() : Promise.reject(r));
  },
  addServer(name, ip, os_type, csrf) {
    return fetch('/api/servers', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ name, ip, os_type })
    }).then(r => r.ok ? r.json() : Promise.reject(r));
  },
  delServer(id, csrf) {
    return fetch(`/api/servers?id=${encodeURIComponent(id)}`, {
      method: 'DELETE',
      headers: { 'X-CSRFToken': csrf }
    }).then(r => r.ok ? r.json() : Promise.reject(r));
  },
  rebootServer(ip, name, csrf) {
    return fetch('/api/reboot', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ ip, name })
    }).then(r => r.ok ? r.json() : Promise.reject(r));
  },
  upgradeServer(ip, csrf) {
    return fetch(`/api/updates?ip=${encodeURIComponent(ip)}`, {
      method: 'GET',
      headers: { 'X-CSRFToken': csrf }
    }).then(r => r.ok ? r.json() : Promise.reject(r));
  },
  getKey() {
    return fetch('/api/key').then(r => r.ok ? r.text() : Promise.reject(r));
  },
  changePassword(oldPassword, newPassword, csrf) {
    return fetch('/api/set_password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrf
      },
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
    }).then(r => r.ok ? r.json() : Promise.reject(r));
  },
  logout(csrf) {
    return fetch('/api/logout', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrf }
    }).then(r => r.ok ? r : Promise.reject(r));
  },
  login(username, password, csrf) {
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
