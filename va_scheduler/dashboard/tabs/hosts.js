var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
var connect = require('react-redux').connect;

var Hosts = React.createClass({
    getInitialState: function () {
        return {hosts: []};
    },
    componentDidMount: function () {
        var me = this;
        Network.get('/api/hosts', this.props.auth.token).done(function (data) {
            //me.setState({hosts: data.hosts});
        });
    },
    render: function() {
        var host_rows = this.state.hosts.map(function(host) {
            return <tr key={host.name}>
                <td>{host.name}</td>
                <td>{host.driver}</td>
                <td>{host.is_deletable ? 'Delete' : '(this host)'}</td>
            </tr>
        });
        var NewHostFormRedux = connect(function(state){
            return {auth: state.auth};
        })(NewHostForm);

        return (<div>
            <NewHostFormRedux />
            <Bootstrap.PageHeader>Current hosts <small>All specified hosts</small></Bootstrap.PageHeader>
            <Bootstrap.Table striped bordered hover>
                <thead>
                    <tr>
                    <td>Host name</td>
                    <td>Driver</td>
                    <td>Actions</td>
                    </tr>
                </thead>
                <tbody>
                    {host_rows}
                </tbody>
            </Bootstrap.Table>
        </div>);
    }
});


var NewHostForm = React.createClass({
    getInitialState: function () {
        return {currentDriver: null, drivers: []};
    },
    componentDidMount: function () {
        var me = this;
        Network.get('/api/drivers', this.props.auth.token).done(function(data) {
            var newState = {drivers: data.drivers};
            if(data.drivers.length > 0){
                newState.currentDriver = data.drivers[0].id;
            }
            me.setState(newState);
        });
    },
    render: function () {
        var steps = [];
        var driverOptions = [];
        for(var i = 0; i < this.state.drivers.length; i++) {
            var driver = this.state.drivers[i];
            driverOptions.push(
                <option value={driver.id} key={driver.id}>{driver.friendly_name}</option>
            );
            if(this.state.currentDriver === driver.id){
                for(var j = 0; j < driver.steps.length; j++){
                    var step = driver.steps[j];
                    steps.push(
                        <Bootstrap.Tab disabled title={step.name} eventKey={step.name} key={step.name} id={step.name} />
                    );
                }
            }
        }

        return (
            <div style={{paddingTop: 10}}>
                <Bootstrap.Panel header='Add host' bsStyle='primary'>
                    <Bootstrap.Tabs defaultActiveKey={1}>
                        <Bootstrap.Tab title='Choose host' eventKey={1} id='1'>
                            <Bootstrap.FormGroup controlId="formControlsSelect">
                                <Bootstrap.ControlLabel>Select host type</Bootstrap.ControlLabel>
                                <Bootstrap.FormControl componentClass="select" placeholder="select">
                                    {driverOptions}
                                </Bootstrap.FormControl>
                            </Bootstrap.FormGroup>
                        </Bootstrap.Tab>
                        {steps}
                    </Bootstrap.Tabs>

                    <Bootstrap.ButtonGroup>
                        <Bootstrap.Button bsStyle='primary'>
                            <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                    </Bootstrap.ButtonGroup>
                </Bootstrap.Panel>
        </div>);
    },
    onChange: function (event) {
        this.setState({currentDriver: event.target.value})
    },
    onSubmit: function(e) {
        e.preventDefault();
        var data = {name: this.refs.hostname.value, driver: this.state.currentDriver};
        Network.post('/api/hosts', this.props.auth.token, data);
    }
});

Hosts = connect(function(state){
    return {auth: state.auth};
})(Hosts);

module.exports = Hosts;
