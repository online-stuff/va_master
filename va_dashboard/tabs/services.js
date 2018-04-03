import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import { connect } from 'react-redux';
var Network = require('../network');
import { Table, Tr, Td } from 'reactable';
import { 
        getTableRowWithActions, 
        getTableRow, 
        getModalHeader, 
        getModalFooter, 
        initializeFields, 
        initializeFieldsWithValues, 
        reduceArr, 
        objArr2str 
    } from './util';
import { ConfirmPopup } from './shared_components';
import Select from 'react-select-plus';

const tblCols = ['Name', 'Address', 'Port', 'Tags', 'Checks'];
const tblCols2 = ['Name', 'Status', 'Output', 'Interval'];
const formInputs = [
    {key: "name", label: "Name", type: "text"}, 
    {key: "address", label: "Address", type: "text"}, 
    {key: "port", label: "Port", type: "text"},
    {key: "tags", label: "Tags", type: "text"}
    //{key: "presets", label: "Checks", type: "select"}
];

class Services extends Component {
    constructor (props) {
        super(props);
        this.state = {
            services: [],
            loading: true,
			popupShow: false,
			popupData: {},
			selectedServiceName: '',
			presets: [],
			checksTableVisible: false
        };
        this.getCurrentServices = this.getCurrentServices.bind(this);
        this.confirm_action = this.confirm_action.bind(this);
        this.deleteService = this.deleteService.bind(this);
		this.addService = this.addService.bind(this);
        this.editService = this.editService.bind(this);
        this.popupClose = this.popupClose.bind(this);
        this.onLinkClick = this.onLinkClick.bind(this);
        this.doAction = this.doAction.bind(this);
        this.editTable = this.editTable.bind(this);
        this.onBackClick = this.onBackClick.bind(this);
    }

	getCurrentServices () {
		Network.get('api/services/get_services_table_data', this.props.auth.token).done(data => {
            let { services, presets } = data;
			this.setState({ services, presets, loading: false });
		}).fail(msg => {
			this.props.dispatch({ type: 'SHOW_ALERT', msg });
		});
	}

    componentDidMount() {
        this.getCurrentServices();
    }

    confirm_action(service){
        var data = { "name": service.name };
        this.setState({ popupShow: true, popupData: data });
    }

    deleteService (data){
        this.popupClose();
        Network.delete('/api/services/delete', this.props.auth.token, data).done(data => {
            this.getCurrentServices();
        }).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }

    addService () {
        this.props.dispatch({ type: 'OPEN_MODAL', modalType: "ADD" });
    }

    editService (service, index) {
        this.props.dispatch({ type: 'OPEN_MODAL', modalType: "EDIT", args: service, rowIndex: index });
    }

	editTable(type, data, i){
        let services = Object.assign([], this.state.services);
        if(type === 'ADD'){
            services.push(data);
        }else {
            services[i] = data;
        }
        this.setState({services});
	}

    popupClose() {
        this.setState({ popupShow: false });
    }

    onLinkClick(serviceName, index) {
		this.setState({ checksTableVisible: true, selectedServiceName: serviceName, checks: this.state.services[index].check});
    }

    onBackClick(){
        this.setState({ checksTableVisible: false });
    }

    doAction(serviceName, index, evtKey) {
        if(evtKey === "Edit"){
            this.editService(serviceName, index);
        }else {
            this.confirm_action(serviceName);
        }
    }

    render() {
        let { services, loading, popupShow, popupData, checksTableVisible, selectedServiceName, checks } = this.state;
        let tblRows = services.map((service, index) => {
			let { name, address, port, tags, check } = service;
            return (
                <Tr key={name}>
                    {getTableRowWithActions(tblCols, [name, address, port, tags, objArr2str(check, 'name')], ['Edit','Delete'], this.doAction, service, this.onLinkClick, index)}
                </Tr>
            );
        });
        const spinnerStyle = {
            display: loading ? "block": "none"
        };
        let blockStyle = {
            display: loading ? "none": "block"
        };
        if(checksTableVisible){
            blockStyle = { display: "none" };
        }
        return ( 
            <div className="app-containter">
                <span className="spinner" style={spinnerStyle} ><i className="fa fa-spinner fa-spin fa-3x" aria-hidden="true"></i></span>
                <div style={blockStyle} className="card">
					<div className="card-body">
						<Table className="table striped" columns={[...tblCols, 'Actions']} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={tblCols} filterable={tblCols} btnName="Add service" btnClick={this.addService} title="Current services" filterClassName="form-control" filterPlaceholder="Filter">
							{tblRows}
						</Table>
					</div>
                </div>
				{ checksTableVisible && <Checks service={selectedServiceName} checks={checks} backAction={this.onBackClick} /> }
                <ModalRedux presetsOptions={this.state.presets} getCurrentServices={this.getCurrentServices} />
				<ConfirmPopup body={"Please confirm action: delete service " + popupData.name} show={popupShow} data={[popupData]} close={this.popupClose} action={this.deleteService} />
            </div> 
        );
    }
}

const Checks = (props) => {
	let { service, checks } = props;
	let tblRows = checks.map(check => {
		let { name, output, status, interval } = check;
		return (
			<Tr key={name}>
				{getTableRow(tblCols2, [name, status, output, interval])}     
			</Tr>
		);
	});
    return (
		<div className="card">
			<div className="card-body">
                <Table className="table striped" columns={tblCols2} itemsPerPage={10} pageButtonLimit={10} noDataText="No matching records found." sortable={tblCols2} filterable={tblCols2} title='Current checks for ' link={service} linkAction={props.backAction} filterClassName="form-control" filterPlaceholder="Filter">
					{tblRows}
				</Table>
			</div>
		</div>
    );
}

class Modal extends Component {
    constructor(props) {
        super(props);
        //let nFormInputs = Object.assign([], formInputs);
        let { modalType, args } = props.modal;
        let fields = initializeFields(formInputs);
        fields.presets = "";
        fields.interval = "";
        fields.timeout = "";
        fields.server = "";
        this.state = fields;
        this.action = this.action.bind(this);
        this.close = this.close.bind(this);
        this.onFieldChange = this.onFieldChange.bind(this);
        this.getInput = this.getInput.bind(this);
        this.onSelectChange = this.onSelectChange.bind(this);
        this.getInputGroup = this.getInputGroup.bind(this);
    }

    componentWillReceiveProps(nextProps){
        let { modalType, args } = nextProps.modal;
        let fields = (modalType === "ADD") ? initializeFields(formInputs) : initializeFieldsWithValues(formInputs, args);
        this.setState({ ...fields });
    }

    onFieldChange(e) {
        let { id, value } = e.target
        this.setState({ [id]: value });
    }

    onSelectChange(key, val) {
        if(key in this.state){
            this.setState({ [key]: val });
        }
    }

    action() {
		let modalType = this.props.modal.modalType;
        let check = modalType === "ADD";
        let endpoint = `/api/services/${check ? 'add_service_with_presets' : 'edit_service_with_presets'}`;
        let data = Object.assign({}, this.state);
        if(check)
            data.presets = reduceArr(data.presets, 'value');
        Network.post(endpoint, this.props.auth.token, data).done(data => {
            //this.props.editTable(modalType, this.state, this.props.modal.rowIndex);
            this.close();
            this.props.getCurrentServices();
        }).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }

    close() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    }

    getInput(type, key) {
        switch(type){
            case 'text':
                return <Bootstrap.FormControl type='text' id={key} value={this.state[key]} onChange={this.onFieldChange} />
            case 'select':
                return <Select name={key} id={key} options={this.props[key + 'Options']} multi={true} value={this.state[key]} onChange={this.onSelectChange.bind(null, key)} />
        }
    }

    getInputGroup(type, key, label) {
		return (
			<Bootstrap.FormGroup key={key}>
				<Bootstrap.ControlLabel >{label}</Bootstrap.ControlLabel>
				{this.getInput(type, key)}
			</Bootstrap.FormGroup>
		);
    }

    render() {
        let { modalType, args } = this.props.modal;
        let inputs = formInputs.map(field => {
            let { type, key, label } = field;
			return this.getInputGroup(type, key, label);
        });
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
                {getModalHeader(modalType === "ADD" ? "Add service" : `Edit service ${args.name}`)}
                <Bootstrap.Modal.Body>
                    <form>
                        {inputs}
                        {modalType === "ADD" && [this.getInputGroup('select', 'presets', 'Checks'), this.getInputGroup('text', 'server', 'Server'), this.getInputGroup('text', 'interval', 'Interval'), this.getInputGroup('text', 'timeout', 'Timeout')]}
                    </form>
                </Bootstrap.Modal.Body>
                {getModalFooter([{label: 'Cancel', onClick: this.close}, {label: modalType === "ADD" ? "Add service" : "Apply change", bsStyle: 'primary', onClick: this.action}])}
            </Bootstrap.Modal>
        );
    }
}

const ModalRedux = connect(function(state){
    return {auth: state.auth, modal: state.modal, alert: state.alert};
})(Modal);

module.exports = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Services);
