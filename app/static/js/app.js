// Define the `lanJanitorApp` module
var app = angular.module('lanJanitor', []);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

// API endpoint constants
const API_SERVERS = "api/servers";
const API_REBOOT = "api/reboot";
const API_UPDATES = "api/updates";
const API_KEY = "api/key";
const API_PASSWORD = "api/set_password";
const API_LOGOUT = "api/logout";

// Define the `lanJanitorController` controller on the `lanJanitorApp` module
app.controller('lanJanitorController', function ($scope, $http) {
    // CSRF token from meta tag
    const csrfToken = document.querySelector('meta[name="csrf-token"]') ? document.querySelector('meta[name="csrf-token"]').getAttribute('content') : '';

    // Helper to add CSRF header
    function csrfConfig(config) {
        config = config || {};
        config.headers = config.headers || {};
        config.headers['X-CSRFToken'] = csrfToken;
        return config;
    }

    // Overlay helpers
    function showOverlay() {
        document.getElementById('overlay').style.display = 'block';
    }
    function hideOverlay() {
        document.getElementById('overlay').style.display = 'none';
    }

    // Get server list
    $scope.getServers = function() {
        $http.get(API_SERVERS)
        .then(function(response) {
            $scope.servers = response.data;
        });
    };

    // Add a server
    $scope.addServer = function(name, ip) {
        $http.post(API_SERVERS, {name: name, ip: ip}, csrfConfig())
        .then(function(response) {
            $scope.newServerName = "";
            $scope.newServerIP = "";
            $scope.getServers();
        });
    };

    // Delete a server
    $scope.delServer = function(id, name) {
        if (confirm("Delete " + name + "?")) {
            $http.delete(API_SERVERS, {params: {id: id}, ...csrfConfig()})
            .then(function(response) {
                $scope.getServers();
            });
        }
    };

    // Reboot a server
    $scope.rebootServer = function(ip, name) {
        if (confirm("Reboot " + name + "? This will restart the server.")) {
            showOverlay();
            $http.post(API_REBOOT, {ip: ip, name: name}, csrfConfig())
            .then(function(response) {
                setTimeout(function() {
                    $scope.getServers();
                    hideOverlay();
                }, 10000); // Wait 10 seconds for reboot
            });
        }
    };

    // Upgrade a server
    $scope.upgradeServer = function(ip, name) {
        if (confirm("Install updates on " + name + "?")) {
            showOverlay();
            $http.get(API_UPDATES, {params: {ip: ip}})
            .then(function(response) {
                $scope.getServers();
                hideOverlay();
            });
        }
    };

    // Get SSH public key
    $scope.getkey = function() {
        $http.get(API_KEY)
        .then(function(response) {
            $scope.publickey = response.data;
        });
    };

    // Change password
    $scope.changePassword = function() {
        $scope.passwordChangeSuccess = false;
        $scope.passwordChangeError = "";
        if ($scope.newPassword !== $scope.confirmPassword) {
            $scope.passwordChangeError = "New passwords do not match.";
            return;
        }
        $http.post(API_PASSWORD, {
            old_password: $scope.currentPassword,
            new_password: $scope.newPassword
        }, csrfConfig())
        .then(function(response) {
            $scope.passwordChangeSuccess = true;
            $scope.currentPassword = "";
            $scope.newPassword = "";
            $scope.confirmPassword = "";
        }, function(error) {
            if (error.status === 401) {
                window.location.href = "/login";
            } else {
                $scope.passwordChangeError = error.data && (error.data.error || error.data.message) ? (error.data.error || error.data.message) : "Password change failed.";
                console.log("Password change error:", error);
            }
        });
    };

    // Logout function
    $scope.logout = function() {
        $http.post(API_LOGOUT, {}, csrfConfig())
        .then(function(response) {
            window.location.href = "/login";
        }, function() {
            window.location.href = "/login";
        });
    };

    // Initial load
    $scope.getServers();
    $scope.getkey();
});