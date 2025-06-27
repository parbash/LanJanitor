// ServerCard Vue component
defaultServerCard = {
  props: ['server'],
  emits: ['delete', 'reboot', 'upgrade'],
  template: `
    <div class="card server-card">
      <div class="card-body">
        <h5 class="card-title d-flex align-items-center gap-2" style="font-family: Staatliches;">
          <i class="bi bi-bucket text-success"></i>
          {{ server.server_name }}
          <i class="bi bi-trash-fill ms-auto text-danger" style="cursor:pointer;" @click="$emit('delete', server.server_id, server.server_name)" title="Delete"></i>
        </h5>
        <h6 class="card-subtitle mb-2 text-muted">{{ server.server_ip }}</h6>
        <div class="mb-2">
          <span class="badge bg-secondary me-2">ID: {{ server.server_id }}</span>
          <span v-if="server.server_updates == -1" class="badge bg-danger"><i class="bi bi-exclamation-triangle-fill me-1"></i>Error</span>
          <span v-else class="badge bg-info text-dark">Updates: {{ server.server_updates }}</span>
        </div>
        <div v-if="server.server_updates == -1" class="alert alert-warning p-2 py-1 mb-2 d-flex align-items-center gap-2">
          <i class="bi bi-exclamation-triangle-fill text-danger"></i>
          <span>Update check failed for this server.</span>
        </div>
        <div v-if="server.server_reboot == 'true'" class="alert alert-danger p-2 py-1 mb-2 d-flex align-items-center gap-2">
          <i class="bi bi-power text-danger"></i>
          <span>This server requires a reboot.</span>
        </div>
        <div class="d-flex align-items-center mb-2">
          <strong class="me-2">Status:</strong>
          <span v-if="server.ping_status == 'online'">
            <i class="bi bi-check-circle-fill text-success" title="Online"></i> Online
          </span>
          <span v-else>
            <i class="bi bi-x-circle-fill text-danger" title="Offline"></i> Offline
          </span>
        </div>
        <div class="d-flex align-items-center gap-2 mt-3">
          <button class="btn btn-warning btn-sm" @click="$emit('reboot', server.server_ip, server.server_name)">
            <i class="bi bi-arrow-repeat"></i> Reboot
          </button>
          <button class="btn btn-primary btn-sm" @click="$emit('upgrade', server.server_ip, server.server_name)">
            <i class="bi bi-tools"></i> Upgrade
          </button>
        </div>
      </div>
    </div>
  `
};
window.ServerCard = defaultServerCard;
