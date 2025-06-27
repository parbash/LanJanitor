// LoadingOverlay Vue component
defaultLoadingOverlay = {
  props: ['show'],
  template: `
    <div class="overlay" v-show="show">
      <div class="d-flex justify-content-center">
        <div class="text-primary" style="position: fixed;top: 30%;">
          Installing updates...
        </div>
        <div class="spinner-border text-primary" role="status" style="position: fixed;top: 40%;width: 3rem; height: 3rem;">
          <span class="visually-hidden">Updating...</span>
        </div>
      </div>
    </div>
  `
};
window.LoadingOverlay = defaultLoadingOverlay;
