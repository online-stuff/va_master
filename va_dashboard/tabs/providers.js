import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
import { connect } from 'react-redux';
import { Table, Tr, Td } from 'reactable';
import { ConfirmPopup } from './shared_components';
import { getTableRowWithAction } from './util';

const tblCols = ['Provider name', 'IP', 'Instances', 'Driver', 'Status'];

class Providers extends Component {
    constructor (props) {
        super(props);
        this.state = {
            providers: [], 
            loading: true, 
            popupShow: false, 
            popupData: {}
        };
        this.getCurrentProviders = this.getCurrentProviders.bind(this);
        this.confirm_action = this.confirm_action.bind(this);
        this.deleteProvider = this.deleteProvider.bind(this);
        this.addProvider = this.addProvider.bind(this);
        this.popupClose = this.popupClose.bind(this);
    }
    getCurrentProviders () {
        Network.post('/api/providers', this.props.auth.token, {}).done(data => {
            this.setState({ providers: data.providers, loading: false });
        }).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }
    componentDidMount() {
        this.getCurrentProviders();
    }
    confirm_action(e){
        var data = { "provider_name": e.target.value };
        this.setState({ popupShow: true, popupData: data });
    }
    deleteProvider (data){
        Network.post('/api/providers/delete', this.props.auth.token, data).done(data => {
            this.getCurrentProviders();
        }).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }
    addProvider () {
        this.props.dispatch({ type: 'OPEN_MODAL' });
    }
    popupClose() {
        this.setState({ popupShow: false });
    }
    render() {
        const { providers, loading, popupData, popupShow } = this.state;
        var provider_rows = providers.map(provider => {
            let { provider_name, provider_ip, servers, driver_name, status } = provider, className;
            if(status.success){
                status = "Online";
                className = "row-provider-Online";
            }else{
                let popover = (
                    <Bootstrap.Popover title="Error">
                        {status.message}
                    </Bootstrap.Popover>
                );
                status = (<Bootstrap.OverlayTrigger overlay={popover}><a>Offline</a></Bootstrap.OverlayTrigger>);
                className = "danger row-provider-Offline";
            }
            return (
                <Tr key={provider.provider_name} className={className}>
                    {getTableRowWithAction(tblCols, [provider_name, provider_ip, servers.length, driver_name, status], 'Delete', provider_name, this.confirm_action)}
                </Tr>
            );
        });
        const spinnerStyle = {
            display: loading ? "block": "none",
        };
        const blockStyle = {
            visibility: loading ? "hidden": "visible",
        };
        return (<div className="app-containter">
            <NewProviderFormRedux changeProviders = {this.getCurrentProviders} />
            <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
            <div style={blockStyle} className="card">
                <div className="card-body">
                    <Table className="table striped" columns={[...tblCols, 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={tblCols} filterable={tblCols} btnName="Add provider" btnClick={this.addProvider} title="Current providers" filterClassName="form-control" filterPlaceholder="Filter">
                        {provider_rows}
                    </Table>
                </div>
            </div>
            <ConfirmPopup body={"Please confirm action: delete provider " + popupData.provider_name} show={popupShow} data={[popupData]} close={this.popupClose} action={this.deleteProvider} />
        </div>);
    }
}

const ProviderStep = (props) => {
    var fields = [];
    for(var i = 0; i < props.fields.length; i++) {
        var field = props.fields[i];
        var formControl = null;
        var notAField = false;
        if(field.type === 'str') {
            formControl = <Bootstrap.FormControl type='text' key={field.id} id={field.id} value={props.fieldValues[field.id]} onChange={props.onFieldChange} />;
        } else if(field.type === 'options') {
            formControl = (
                <Bootstrap.FormControl componentClass='select' key={field.id} id={field.id} onChange={props.onFieldChange}>
                    <option key={-1} value=''>Choose</option>
                    {props.optionChoices[field.id].map(function(option, i) {
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
                        <p>{props.optionChoices[field.id]}</p>
                    </Bootstrap.Well>
                </Bootstrap.FormGroup>
            );
        }
        else if(field.type === 'file'){
            formControl = <Bootstrap.FormControl type='file' key={field.id} id={field.id} value={props.fieldValues[field.id]} onChange={props.onFieldChange} />;
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
}

class NewProviderForm extends Component {
    constructor (props) {
        super(props);
        this.state = {currentDriver: null, drivers: [], stepIndex: -1, optionChoices: {},
            errors: [], fieldValues: {}, isLoading: false};
        this.onDriverSelect = this.onDriverSelect.bind(this);
        this.onFieldChange = this.onFieldChange.bind(this);
        this.close = this.close.bind(this);
        this.nextStep = this.nextStep.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }
    componentDidMount () {
        Network.get('/api/drivers', this.props.auth.token).done(data => {
            this.setState({ drivers: data.drivers });
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg});
        });
    }
    onDriverSelect (e) {
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
    }
    onFieldChange(e){
        let id = e.target.id;
        let value = e.target.value;
        let newFieldValues = Object.assign({}, this.state.fieldValues);
        newFieldValues[id] = value;
        this.setState({fieldValues: newFieldValues});
    }
    close() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    }
    render() {
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
    }
    nextStep() {
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
    }
    onSubmit(e) {
        e.preventDefault();
        var data = {name: this.refs.provider_name.value, driver: this.state.currentDriver};
        var me = this;
        Network.post('/api/providers', this.props.auth.token, data).done(function(data) {
            me.props.changeProviders();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
}

const NewProviderFormRedux = connect(function(state){
	return {auth: state.auth, alert: state.alert, modal: state.modal};
})(NewProviderForm);

module.exports = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Providers);

