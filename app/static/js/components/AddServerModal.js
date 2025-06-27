// AddServerModal Vue component
defaultAddServerModal = {
  props: ['name', 'ip', 'os_type'],
  emits: ['update:name', 'update:ip', 'update:os_type', 'add'],
  template: `
  <div class="modal fade" id="serverModal" tabindex="-1" aria-labelledby="serverModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="serverModalLabel">Add Server</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <div class="row g-3">
            <div class="col">
              <input type="text" class="form-control" id="newServerName" :value="name" @input="$emit('update:name', $event.target.value)" placeholder="Server Name">
            </div>
            <div class="col">
              <input type="text" class="form-control" id="newServerIP" :value="ip" @input="$emit('update:ip', $event.target.value)" placeholder="Server IP">
            </div>
          </div>
          <div class="row g-3 mt-2">
            <div class="col">
              <label for="osTypeSelect" class="form-label">Operating System</label>
              <select id="osTypeSelect" class="form-select" :value="os_type" @change="$emit('update:os_type', $event.target.value)">
                <option value="Ubuntu">Ubuntu</option>
                <option value="Windows">Windows</option>
                <option value="Other Linux">Other Linux</option>
              </select>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
          <button class="btn btn-primary" @click="$emit('add')" data-bs-dismiss="modal">Add</button>
        </div>
      </div>
    </div>
  </div>
  `
};
window.AddServerModal = defaultAddServerModal;
