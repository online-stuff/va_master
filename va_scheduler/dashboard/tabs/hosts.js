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

var HostStep = React.createClass({
    render: function () {
        var fields = [];
        for(var i = 0; i < this.props.fields.length; i++) {
            var field = this.props.fields[i];
            var formControl = null;
            var notAField = false;
            if(field.type === 'str') {
                formControl = <Bootstrap.FormControl type='text' id={field.id} value={this.props.fieldValues[field.id]} onChange={this.onChange} />;
            } else if(field.type === 'options') {
                formControl = (
                    <Bootstrap.FormControl componentClass='select' id={field.id} onChange={this.onChange}>
                        <option key={-1} value=''>Choose</option>
                        {this.props.optionChoices[field.id].map(function(option, i) {
                            return <option key={i} value={option}>{option}</option>
                        })}
                    </Bootstrap.FormControl>
                );
            } else if(field.type === 'description'){
                notAField = true;
                formControl = (
                    <Bootstrap.FormGroup>
                        <br/>
                        <Bootstrap.Well>
                            <h4>
                            {field.name} &nbsp;
                            <Bootstrap.Label bsStyle='info'> Info</Bootstrap.Label>
                            </h4>
                            <p>{this.props.optionChoices[field.id]}</p>
                        </Bootstrap.Well>
                    </Bootstrap.FormGroup>
                );
            }
            if(notAField) {
                fields.push(formControl);
            } else {
                fields.push(
                    <Bootstrap.FormGroup>
                        <Bootstrap.ControlLabel >{field.name}</Bootstrap.ControlLabel>
                        {formControl}
                    </Bootstrap.FormGroup>
                );
            }
        }
        return (
            <form>
                {fields}
            </form>
        )
    },
    onChange: function(e) {
        this.props.onFieldChange(e.target.id, e.target.value);
    }
});

var NewHostForm = React.createClass({
    getInitialState: function () {
        return {currentDriver: null, drivers: [], stepIndex: -1, optionChoices: {},
            errors: [], fieldValues: {}};
    },
    componentDidMount: function () {
        var me = this;
        Network.get('/api/drivers', this.props.auth.token).done(function(data) {
            var newState = {drivers: data.drivers};
            me.setState(newState);
        });
    },
    onDriverSelect: function (e) {
        var driverId = e.target.value;
        for(var i = 0; i < this.state.drivers.length; i++){
            var driver = this.state.drivers[i];
            if(driver.id === driverId) {
                var fieldVals = {};
                var optionChoices = {};
                for(var j = 0; j < driver.steps.length; j++){
                    var step = driver.steps[j];
                    for(var k = 0; k < step.fields.length; k++){
                        var field = step.fields[k];
                        fieldVals[field.id] = '';
                        if(field.type == 'options' || field.type == 'description') {
                            optionChoices[field.id] = [];
                        }
                    }
                }
                this.setState({currentDriver: driver, stepIndex: -1, optionChoices: optionChoices,
                    errors: [], fieldValues: fieldVals});
                return;
            }
        }
        this.setState({currentDriver: null, stepIndex: -1, optionChoices: {},
            errors: [], fieldValues: {}});
    },
    onFieldChange: function(id, value){
        var newFieldValues = Object.assign({}, this.state.fieldValues);
        newFieldValues[id] = value;
        this.setState({fieldValues: newFieldValues});
    },
    render: function () {
        console.log(this.state);
        var steps = [];
        var driverOptions = [<option value=''>Select driver</option>];
        for(var i = 0; i < this.state.drivers.length; i++) {
            var driver = this.state.drivers[i];
            driverOptions.push(
                <option value={driver.id} key={driver.id}>{driver.friendly_name}</option>
            );
            if(this.state.currentDriver !== null) {
                for(var j = 0; j < this.state.currentDriver.steps.length; j++){
                    var step = this.state.currentDriver.steps[j];
                    if(j !== this.state.stepIndex){
                        steps.push(
                            <Bootstrap.Tab title={step.name} eventKey={j} key={j} />
                        );
                    }else{
                        steps.push(
                            <Bootstrap.Tab title={step.name} eventKey={j} key={j}>
                                <HostStep fields={step.fields} optionChoices={this.state.optionChoices}
                                    fieldValues={this.state.fieldValues}
                                    onFieldChange={this.onFieldChange}/>
                            </Bootstrap.Tab>
                        );
                    }
                }
            }
        }

        var errors = [];
        for(var i = 0; i < this.state.errors.length; i++){
            var err = this.state.errors[i];
            errors.push(
                <Bootstrap.Alert bsStyle='danger'>{err}</Bootstrap.Alert>
            );
        }

        return (
            <div style={{paddingTop: 10}}>
                <Bootstrap.Panel header='Add host' bsStyle='primary'>
                    <Bootstrap.Tabs activeKey={this.state.stepIndex}>
                        <Bootstrap.Tab title='Choose host' eventKey={-1}>
                            <Bootstrap.FormGroup controlId="formControlsSelect">
                                <Bootstrap.ControlLabel>Select host type</Bootstrap.ControlLabel>
                                <Bootstrap.FormControl componentClass="select" onChange={this.onDriverSelect} placeholder="select">
                                    {driverOptions}
                                </Bootstrap.FormControl>
                            </Bootstrap.FormGroup>
                        </Bootstrap.Tab>
                        {steps}
                    </Bootstrap.Tabs>

                    {errors}
                    <Bootstrap.ButtonGroup>
                        <Bootstrap.Button bsStyle='primary' onClick={this.nextStep}>
                            <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                    </Bootstrap.ButtonGroup>
                </Bootstrap.Panel>
        </div>);
    },
    nextStep: function () {
        if(this.state.currentDriver === null) return;
        if(this.state.stepIndex === -1){
            var me = this;
            var data = {driver_id: this.state.currentDriver.id, step_index: -1, field_values: {}};
            Network.post('/api/hosts/new/validate_fields', this.props.auth.token, data).done(function(d) {
                me.setState({stepIndex: d.new_step_index, optionChoices: d.option_choices});
            });
        } else {
            var me = this;
            var data = {driver_id: this.state.currentDriver.id, step_index: this.state.stepIndex,
                field_values: this.state.fieldValues};
            Network.post('/api/hosts/new/validate_fields', this.props.auth.token, data).done(function(d) {
                var mergeChoices = Object.assign({}, me.state.optionChoices);
                for(var id in d.option_choices){
                    mergeChoices[id] = d.option_choices[id];
                }
                me.setState({stepIndex: d.new_step_index, optionChoices: mergeChoices, errors: d.errors});
            });
            //var data = {driver_id: this.state.currentDriver.id, current_index: this.state.stepIndex,
            //}
        }
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
