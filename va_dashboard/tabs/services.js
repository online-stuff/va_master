import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import { connect } from 'react-redux';
var Network = require('../network');
import { Table, Tr, Td } from 'reactable';
import { getTableRowsWithActions } from './util';
import { ConfirmPopup } from './shared_components';

const tblCols = ['Name', 'Address', 'Port'];

class Services extends Component {
    constructor (props) {
        super(props);
        this.state = {
            services: [],
            loading: true,
			popupShow: false,
			popupData: {}

        };
        this.getCurrentServices = this.getCurrentServices.bind(this);
        this.confirm_action = this.confirm_action.bind(this);
        this.deleteService = this.deleteService.bind(this);
		this.addService = this.addService.bind(this);
        this.editService = this.editService.bind(this);
        this.popupClose = this.popupClose.bind(this);
        this.doAction = this.doAction.bind(this);
    }

	getCurrentServices () {
		Network.get('api/services/get_services_table_data', this.props.auth.token).done(data => {
			this.setState({ services: data, loading: false });
		}).fail(msg => {
			this.props.dispatch({ type: 'SHOW_ALERT', msg });
		});
	}

    componentDidMount() {
        this.getCurrentServices();
    }

    confirm_action(serviceName){
        var data = { "name": serviceName };
        this.setState({ popupShow: true, popupData: data });
    }

    deleteService (data){
        Network.post('/api/service/delete', this.props.auth.token, data).done(data => {
            this.getCurrentServices();
        }).fail(msg => {
            this.props.dispatch({ type: 'SHOW_ALERT', msg });
        });
    }

    addService () {
        //this.props.dispatch({ type: 'OPEN_MODAL' });
    }

    editService (serviceName) {
        //this.props.dispatch({ type: 'OPEN_MODAL' });
    }

    popupClose() {
        this.setState({ popupShow: false });
    }

    doAction(serviceName, evtKey) {
        if(evtKey === "Edit"){
            this.editService(serviceName);
        }else {
            this.confirm_action(serviceName);
        }
    }

    render() {
        let { services, loading, popupShow, popupData } = this.state;
        let tblRows = services.map(service => {
			let { name, address, port } = service;
            return (
                <Tr key={name}>
                    {getTableRowsWithActions(tblCols, [name, address, port], ['Edit','Delete'], this.doAction, name)}
                </Tr>
            );
        });
        const spinnerStyle = {
            display: loading ? "block": "none"
        };
        const blockStyle = {
            visibility: loading ? "hidden": "visible"
        };
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
				<ConfirmPopup body={"Please confirm action: delete service " + popupData.name} show={popupShow} data={[popupData]} close={this.popupClose} action={this.deleteService} />
            </div> 
        );
    }
}

module.exports = connect(function(state){
    return {auth: state.auth, alert: state.alert};
})(Services);
