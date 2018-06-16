import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var Network = require('../network');
import { connect } from 'react-redux';
import { Table, Tr, Td } from 'reactable';
import { ConfirmPopup } from './shared_components';
import { getModalHeader, getModalFooter, getFormFields, getTableRowWithActions, getSpinner, findObjInArr } from './util';

const tblCols = ['Provider name', 'IP', 'Instances', 'Driver', 'Status'];

class Providers extends Component {
    constructor (props) {
        super(props);
        this.state = {
            providers: [], 
            loading: true, 
            popupShow: false, 
            popupData: {},
            selectedProvider: {},
            drivers: [],
            currentDriver: null,
            fieldValues: {},
            stepIndex: -1
        };
        this.getCurrentProviders = this.getCurrentProviders.bind(this);
        this.confirm_action = this.confirm_action.bind(this);
        this.deleteProvider = this.deleteProvider.bind(this);
        this.addProvider = this.addProvider.bind(this);
        this.editProvider = this.editProvider.bind(this);
        this.popupClose = this.popupClose.bind(this);
        this.doAction = this.doAction.bind(this);
        this.getDrivers = this.getDrivers.bind(this);
        this.getSteps = this.getSteps.bind(this);
        this.reloadProviders = this.reloadProviders.bind(this);
    }
    getCurrentProviders () {
        return Network.post('/api/providers', this.props.auth.token, {}).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }
    reloadProviders () {
        this.getCurrentProviders().done(data => this.setState({ providers: data.providers }));
    }
    getDrivers () {
		return Network.get('/api/drivers', this.props.auth.token).fail(msg => {
			this.props.dispatch({type: 'SHOW_ALERT', msg});
		});
    }
    getSteps(param, selectedProvider) {
        Network.get('/api/providers/get_provider_fields', this.props.auth.token, param).done(data => {
            //this.setState({ currentDriver: {id: this.props.provider.driver_name, steps: data}, fieldValues: this.props.provider, stepIndex: 0 });
			let fieldValues = {};
			for (var j = 0; j < data.steps.length; j++) {
				var step = data.steps[j];
				for (var k = 0; k < step.fields.length; k++) {
					var field = step.fields[k];
					fieldValues[field.id] = field.value;
				}
			}
            this.setState({selectedProvider, currentDriver: data, fieldValues, stepIndex: 0});
        }).fail(msg => {
            this.props.dispatch({type: 'SHOW_ALERT', msg});
        });
    }
    componentDidMount() {
        let n1 = this.getCurrentProviders();
        let n2 = this.getDrivers();
        $.when( n1, n2 ).done((resp1, resp2) => {
            this.setState({ providers: resp1.providers, drivers: resp2.drivers, loading: false });
        });
    }
    confirm_action(provider_name){
        this.setState({ popupShow: true, popupData: {provider_name} });
    }
    deleteProvider (data){
        Network.post('/api/providers/delete', this.props.auth.token, data).done(data => {
            this.reloadProviders();
        }).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }
    addProvider () {
        this.setState({currentDriver: null, stepIndex: -1, fieldValues: {}});
        this.props.dispatch({ type: 'OPEN_MODAL', modalType: 'add' });
    }
    popupClose() {
        this.setState({ popupShow: false });
    }
    editProvider(index) {
        let selectedProvider = this.state.providers[index];
        //let currentDriver = findObjInArr(this.state.drivers, 'id', selectedProvider.driver_name);
        //this.setState({selectedProvider: this.state.providers[index], currentDriver});
        this.getSteps({provider_name: selectedProvider.provider_name}, selectedProvider);
        this.props.dispatch({ type: 'OPEN_MODAL', modalType: 'edit' });
    }
    doAction(providerName, index, evtKey) {
        if(evtKey === "Edit"){
            this.editProvider(index);
        }else {
            this.confirm_action(providerName);
        }
    }
    render() {
        const { providers, loading, popupData, popupShow } = this.state;
        var provider_rows = providers.map((provider, i) => {
            let { provider_name, provider_ip, servers, driver_name, status } = provider, className;
            if(status.success){
                status = "Online";
                // className = "row-provider-Online";
            }else{
                let popover = (
                    <Bootstrap.Popover title="Error">
                        {status.message}
                    </Bootstrap.Popover>
                );
                status = (<Bootstrap.OverlayTrigger overlay={popover}><a>Offline</a></Bootstrap.OverlayTrigger>);
                // className = "danger row-provider-Offline"; 
                // keep style consistency, no more custom css
            }
            return (
                <Tr key={provider.provider_name} className={className}>
                    {getTableRowWithActions(tblCols, [provider_name, provider_ip, servers.length, driver_name, status], ['Delete', 'Edit'], this.doAction, provider_name, null, i)}
                </Tr>
            );
        });
        const blockStyle = {
            visibility: loading ? "hidden": "visible"
        };
        return (<div className="app-containter">
            <NewProviderFormRedux reload = {this.reloadProviders} drivers={this.state.drivers} fieldValues = {this.state.fieldValues} currentDriver={this.state.currentDriver} stepIndex={this.state.stepIndex} />
            {loading && getSpinner()}
            <div style={blockStyle} className="card">
                <div className="card-body">
                    <Table className="table striped" columns={[...tblCols, 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={tblCols} filterable={tblCols} buttons={[{name: "Add provider", onClick: this.addProvider, icon: 'glyphicon glyphicon-plus'}]} title="Current providers" filterClassName="form-control" filterPlaceholder="Filter">
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
                <Bootstrap.FormControl componentClass='select' key={field.id} id={field.id} onChange={props.onFieldChange} value={props.fieldValues[field.id]}>
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
        this.state = {currentDriver: null, stepIndex: props.stepIndex, optionChoices: {},
            errors: [], fieldValues: {}, isLoading: false};
        this.onDriverSelect = this.onDriverSelect.bind(this);
        this.onFieldChange = this.onFieldChange.bind(this);
        this.close = this.close.bind(this);
        this.nextStep = this.nextStep.bind(this);
        this.onSubmit = this.onSubmit.bind(this);
    }
    componentWillReceiveProps(nextProps){
        if(nextProps.currentDriver)
            this.setState({currentDriver: nextProps.currentDriver, optionChoices: nextProps.currentDriver.optionChoices, fieldValues: nextProps.fieldValues, stepIndex: nextProps.stepIndex});
        else
            this.setState({ fieldValues: nextProps.fieldValues, stepIndex: nextProps.stepIndex });
    }
    getDriverOptions(){
        var driverOptions = [<option key="-1" value=''>Select driver</option>];
        for(let i = 0; i < this.props.drivers.length; i++) {
            var driver = this.props.drivers[i];
            driverOptions.push(
                <option value={driver.id} key={driver.id}>{driver.friendly_name}</option>
            );
        }
		return driverOptions;
    }
    onDriverSelect (e) {
        let fieldValues = {}, optionChoices = {};
        let currentDriver = findObjInArr(this.props.drivers, 'id', e.target.value); 
        if(currentDriver) {
            for(var j = 0; j < currentDriver.steps.length; j++){
                var step = currentDriver.steps[j];
                for(var k = 0; k < step.fields.length; k++){
                    var field = step.fields[k];
                    fieldValues[field.id] = '';
                    if(field.type == 'options' || field.type == 'description') {
                        optionChoices[field.id] = [];
                    }
                }
            }
        }
        this.setState({ currentDriver, stepIndex: -1, optionChoices, errors: [], fieldValues });
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
        let typeCheck = this.props.modal.modalType === 'edit';
        let stepIndex = this.state.stepIndex;
        if(this.state.currentDriver !== null) {
            let currentDriver = this.state.currentDriver;
            for(var j = 0; j < currentDriver.steps.length; j++){
                var step = currentDriver.steps[j];
                if(j !== stepIndex){
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
        for(let i = 0; i < this.state.errors.length; i++){
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
                {getModalHeader(typeCheck ? 'Edit provider' : 'Add provider')}

                <Bootstrap.Modal.Body>
                    {progressBar}
                    <Bootstrap.Tabs id="tabs" activeKey={stepIndex}>
                        { !typeCheck && <Bootstrap.Tab title='Choose provider' eventKey={-1}>
                            <Bootstrap.FormGroup controlId="formControlsSelect">
                                <Bootstrap.ControlLabel>Select provider type</Bootstrap.ControlLabel>
                                <Bootstrap.FormControl componentClass="select" onChange={this.onDriverSelect} placeholder="select">
                                    {this.getDriverOptions()}
                                </Bootstrap.FormControl>
                            </Bootstrap.FormGroup>
                        </Bootstrap.Tab> }
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
            let data = {driver_id: this.state.currentDriver.id, step_index: -1, field_values: {}};
            Network.post('/api/providers/new/validate_fields', this.props.auth.token, data).done(d => {
                this.setState({stepIndex: d.new_step_index, optionChoices: d.option_choices});
            }).fail(msg => {
                this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        } else {
            this.setState({isLoading: true});
            let data = {driver_id: this.state.currentDriver.id, step_index: this.state.stepIndex,
                field_values: this.state.fieldValues};
            let typeCheck = this.props.modal.modalType === 'edit';
            let requestFunc = typeCheck ? Network.put : Network.post;
            requestFunc('/api/providers/new/validate_fields', this.props.auth.token, data).done(d => {
                var mergeChoices = Object.assign({}, this.state.optionChoices);
                for(var id in d.option_choices){
                    mergeChoices[id] = d.option_choices[id];
                }
                if(d.new_step_index == -1 && d.errors.length == 0){
                    setTimeout(() => {
                        this.props.reload();
                    }, 2000);
                }else{
                    this.setState({stepIndex: d.new_step_index, optionChoices: mergeChoices, errors: d.errors, isLoading: false});
                }
            }).fail(msg => {
                this.props.dispatch({type: 'SHOW_ALERT', msg: msg});
            });
        }
    }
    onSubmit(e) {
        e.preventDefault();
        var data = {name: this.refs.provider_name.value, driver: this.state.currentDriver};
        var me = this;
        Network.post('/api/providers', this.props.auth.token, data).done(function(data) {
            this.close();
            me.props.reload();
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

