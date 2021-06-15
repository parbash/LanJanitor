// Define the `phonecatApp` module
var app = angular.module('lanJanitor', []);

app.config(['$interpolateProvider', function($interpolateProvider) {
    $interpolateProvider.startSymbol('{a');
    $interpolateProvider.endSymbol('a}');
}]);

// Define the `PhoneListController` controller on the `phonecatApp` module
app.controller('lanJanitorController', function ($scope, $http) {

    $scope.getServers = function(){
        $http.get("api/servers")
        .then(function(response) {
            $scope.servers = response.data;
        });
    }

    $scope.addServer = function(_name,_ip){
        $http.post("api/servers",{name:_name, ip:_ip})
        .then(function(response) {
            $scope.newServerName="";
            $scope.newServerIP="";
            $scope.getServers();
        });
    }

    $scope.delServer = function(_id,_name){
        if (confirm("Delete " + _name + "?")){
            $http.delete("api/servers",{params: {id: _id}})
            .then(function(response){
                $scope.getServers();
            });
        }
    }

    $scope.getkey = function(){
        $http.get("api/key")
        .then(function(response) {
            $scope.publickey = response.data;
        });
    }

    $scope.getServers();
    $scope.getkey();
});