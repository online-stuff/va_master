var React = require('react');
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
var connect = require('react-redux').connect;
var Reactable = require('reactable');

var Providers = React.createClass({
    getInitialState: function () {
        return {providers: [], loading: true, popupShow: false, popupData: {}};
    },
    getCurrentProviders: function () {
        var me = this;
        Network.post('/api/providers', this.props.auth.token, {}).done(function (data) {
            me.setState({providers: data.providers, loading: false});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },
    componentDidMount: function () {
        this.getCurrentProviders();
    },
    confirm_action: function(e){
        var data = {"provider_name": e.target.value};
        this.setState({popupShow: true, popupData: data});
    },
    deleteProvider: function (data){
        var me = this;
        /*Network.post('/api/providers/delete', this.props.auth.token, data).done(function(data) {
            me.getCurrentProviders();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });*/
    },
    addProvider: function () {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },
    popupClose: function() {
        this.setState({popupShow: false});
    },
    render: function() {
        var provider_rows = this.state.providers.map(function(provider) {
            var status = "", className = "";
            if(provider.status.success){
                status = "Online";
                className = "row-provider-Online";
            }else{
                popover = (
                    <Bootstrap.Popover title="Error">
                        {provider.status.message}
                    </Bootstrap.Popover>
                );
                status = (<Bootstrap.OverlayTrigger overlay={popover}><a>Offline</a></Bootstrap.OverlayTrigger>);
                className = "danger row-provider-Offline";
            }
            return (
                <Reactable.Tr key={provider.provider_name} className={className}>
                    <Reactable.Td column="Provider name">{provider.provider_name}</Reactable.Td>
                    <Reactable.Td column="IP">{provider.provider_ip}</Reactable.Td>
                    <Reactable.Td column="Instances">{provider.servers.length}</Reactable.Td>
                    <Reactable.Td column="Driver">{provider.driver_name}</Reactable.Td>
                    <Reactable.Td column="Status">{status}</Reactable.Td>
                    <Reactable.Td column="Actions"><Bootstrap.Button type="button" bsStyle='primary' onClick={this.confirm_action} value={provider.provider_name}>
                        Delete
                    </Bootstrap.Button></Reactable.Td>
                </Reactable.Tr>
            );
        }.bind(this));
        var NewProviderFormRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert, modal: state.modal};
        })(NewProviderForm);
        var loading = this.state.loading;
        const spinnerStyle = {
            display: loading ? "block": "none",
        };
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
        };
        var sf_cols = ['Provider name', 'IP', 'Instances', 'Driver', 'Status'];
        return (<div className="app-containter">
            <NewProviderFormRedux changeProviders = {this.getCurrentProviders} />
            <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
            <div style={blockStyle}>
                <Bootstrap.PageHeader>Current providers</Bootstrap.PageHeader>
                <Reactable.Table className="table striped" columns={['Provider name', 'IP', 'Instances', 'Driver', 'Status', 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={sf_cols} filterable={sf_cols} btnName="Add provider" btnClick={this.addProvider}>
                    {provider_rows}
                </Reactable.Table>
            </div>
            <ConfirmPopup show={this.state.popupShow} data={this.state.popupData} close={this.popupClose} action={this.deleteProvider} />
        </div>);
    }
});

var ProviderStep = React.createClass({
    render: function () {
        var fields = [];
        for(var i = 0; i < this.props.fields.length; i++) {
            var field = this.props.fields[i];
            var formControl = null;
            var notAField = false;
            if(field.type === 'str') {
                formControl = <Bootstrap.FormControl type='text' key={field.id} id={field.id} value={this.props.fieldValues[field.id]} onChange={this.onChange} />;
            } else if(field.type === 'options') {
                formControl = (
                    <Bootstrap.FormControl componentClass='select' key={field.id} id={field.id} onChange={this.onChange}>
                        <option key={-1} value=''>Choose</option>
                        {this.props.optionChoices[field.id].map(function(option, i) {
                            return <option key={i} value={option}>{option}</option>
                        })}
                    </Bootstrap.FormControl>
                );
            } else if(field.type === 'description'){
                notAField = true;
                formControl = (
                    <Bootstrap.FormGroup key={field.id}>
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
            else if(field.type === 'file'){
                formControl = <Bootstrap.FormControl type='file' key={field.id} id={field.id} value={this.props.fieldValues[field.id]} onChange={this.onChange} />;
            }
            if(notAField) {
                fields.push(formControl);
            } else {
                fields.push(
                    <Bootstrap.FormGroup key={field.id}>
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

var NewProviderForm = React.createClass({
    getInitialState: function () {
        return {currentDriver: null, drivers: [], stepIndex: -1, optionChoices: {},
            errors: [], fieldValues: {}, isLoading: false};
    },
    componentDidMount: function () {
        var me = this;
        Network.get('/api/drivers', this.props.auth.token).done(function(data) {
            var newState = {drivers: data.drivers};
            me.setState(newState);
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
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
    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },
    render: function () {
        var steps = [];
        var driverOptions = [<option key="-1" value=''>Select driver</option>];
        for(var i = 0; i < this.state.drivers.length; i++) {
            var driver = this.state.drivers[i];
            driverOptions.push(
                <option value={driver.id} key={driver.id}>{driver.friendly_name}</option>
            );
        }
        if(this.state.currentDriver !== null) {
            console.log(this.state.currentDriver);
            for(var j = 0; j < this.state.currentDriver.steps.length; j++){
                var step = this.state.currentDriver.steps[j];
                if(j !== this.state.stepIndex){
                    steps.push(
                        <Bootstrap.Tab title={step.name} eventKey={j} key={j} />
                    );
                }else{
                    steps.push(
                        <Bootstrap.Tab title={step.name} eventKey={j} key={j}>
                            <ProviderStep fields={step.fields} optionChoices={this.state.optionChoices}
                                fieldValues={this.state.fieldValues}
                                onFieldChange={this.onFieldChange}/>
                        </Bootstrap.Tab>
                    );
                }
            }
        }

        var errors = [];
        for(var i = 0; i < this.state.errors.length; i++){
            var err = this.state.errors[i];
            errors.push(
                <Bootstrap.Alert key={i} bsStyle='danger'>{err}</Bootstrap.Alert>
            );
        }

        var progressBar = null;
        if(this.state.isLoading) {
            progressBar = <Bootstrap.ProgressBar active now={100} />;
        }

        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Add provider</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    {progressBar}
                    <Bootstrap.Tabs id="add-provider" activeKey={this.state.stepIndex}>
                        <Bootstrap.Tab title='Choose provider' eventKey={-1}>
                            <Bootstrap.FormGroup controlId="formControlsSelect">
                                <Bootstrap.ControlLabel>Select provider type</Bootstrap.ControlLabel>
                                <Bootstrap.FormControl componentClass="select" onChange={this.onDriverSelect} placeholder="select">
                                    {driverOptions}
                                </Bootstrap.FormControl>
                            </Bootstrap.FormGroup>
                        </Bootstrap.Tab>
                        {errors}
                        {steps}
                    </Bootstrap.Tabs>
                </Bootstrap.Modal.Body>

                <Bootstrap.Modal.Footer>
                    <Bootstrap.ButtonGroup>
                        <Bootstrap.Button disabled={this.state.isLoading} bsStyle='primary' onClick={this.nextStep}>
                            <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                    </Bootstrap.ButtonGroup>
                </Bootstrap.Modal.Footer>
            </Bootstrap.Modal>);
    },
    nextStep: function () {
        if(this.state.currentDriver === null) return;
        if(this.state.stepIndex === -1){
            var me = this;
            var data = {driver_id: this.state.currentDriver.id, step_index: -1, field_values: {}};
            Network.post('/api/providers/new/validate_fields', this.props.auth.token, data).done(function(d) {
                me.setState({stepIndex: d.new_step_index, optionChoices: d.option_choices});
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        } else {
            var me = this;
            me.setState({isLoading: true});
            var data = {driver_id: this.state.currentDriver.id, step_index: this.state.stepIndex,
                field_values: this.state.fieldValues};
            Network.post('/api/providers/new/validate_fields', this.props.auth.token, data).done(function(d) {
                var mergeChoices = Object.assign({}, me.state.optionChoices);
                for(var id in d.option_choices){
                    mergeChoices[id] = d.option_choices[id];
                }
                if(d.new_step_index == -1 && d.errors.length == 0){
                    setTimeout(function(){
                         me.props.changeProviders();
                    }, 2000);
                }else{
                    me.setState({stepIndex: d.new_step_index, optionChoices: mergeChoices, errors: d.errors, isLoading: false});
                }
            }).fail(function (msg) {
                me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
            //var data = {driver_id: this.state.currentDriver.id, current_index: this.state.stepIndex,
            //}
        }
    },
    onSubmit: function(e) {
        e.preventDefault();
        var data = {name: this.refs.provider_name.value, driver: this.state.currentDriver};
        var me = this;
        Network.post('/api/providers', this.props.auth.token, data).done(function(data) {
            me.props.changeProviders();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
});

var ConfirmPopup = React.createClass({
    render: function () {
        return (
            <Bootstrap.Modal show={this.props.show} onHide={this.props.close}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Confirm action</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    <p>Please confirm action: delete provider {this.props.data.provider_name}</p>
                </Bootstrap.Modal.Body>

                <Bootstrap.Modal.Footer>
                    <Bootstrap.Button onClick={this.props.close}>Cancel</Bootstrap.Button>
                    <Bootstrap.Button onClick={this.props.action.bind(null, this.props.data)} bsStyle = "primary">Confirm</Bootstrap.Button>
                </Bootstrap.Modal.Footer>
            </Bootstrap.Modal>
        );
    }
});

Providers = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Providers);

module.exports = Providers;
