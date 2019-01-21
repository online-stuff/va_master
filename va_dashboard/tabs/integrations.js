import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var classNames = require('classnames');
import { connect } from 'react-redux';
var Network = require('../network');
import { getSpinner } from './util';
import ReactJson from 'react-json-view'


class Integrations extends Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: true,
            showModal: false,
            stepIndex: 1,
            apps:[],
            events: [],
            eventsPerApp: [],
            actionsPerApp: [],
            selectedDonorApp: '',
            selectedReceiverApp: '',
            selectedEvent: '',
            selectedAction: ''
        };
        this.openTriggerModal=this.openTriggerModal.bind(this);
        this.closeModal=this.closeModal.bind(this);
        this.nextStep=this.nextStep.bind(this);
        this.addTrigger=this.addTrigger.bind(this);
        this.showModalButtons=this.showModalButtons.bind(this);
        this.getApps=this.getApps.bind(this);
        this.getEvents=this.getEvents.bind(this);
        this.getEventsPerApp=this.getEventsPerApp.bind(this);
        this.getAppPerName=this.getAppPerName.bind(this);
        this.reloadModal=this.reloadModal.bind(this);
        this.showEventsSelect=this.showEventsSelect.bind(this);
        this.showActionsSelect=this.showActionsSelect.bind(this);
    }

    componentDidMount() {
        var me=this;
        me.setState({loading: false});
        this.getApps();
    }


    reloadModal(){
        console.log('RELOAD MODAL');
        console.log('Apps', this.state.apps);
        this.getEventsPerApp(this.state.apps[0].name);
        this.getActionsPerApp(this.state.apps[0].name);
        this.setState({selectedDonorApp: '', selectedReceiverApp: '', selectedEvent: '', selectedAction: ''});
    }

    openTriggerModal(){
        this.setState({showModal: true});
    }

    getAppPerName(appName){
        return this.state.apps.filter(app => app.name == appName)[0];
    }

    getApps(){
        var me=this;
        console.log('Calling get apps');
        Network.get('/api/states', this.props.auth.token)
        .done(function (data){
            var result = data;
            var app_list=[];
            result.forEach(function(appObject){
                app_list.push(appObject);
            });
            if(app_list.length > 0){
                me.setState({selectedDonorApp: app_list[0]});
            }
            me.setState({apps: app_list});
            me.getEvents();
        })
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    getEvents(){
        var me=this;
        Network.get('/api/panels/get_functions', this.props.auth.token)
        .done(function (data){
            var result = data;
            var event_list=[];
            result.forEach(function(functionObject){
                event_list.push(functionObject);
            });
            me.setState({events: event_list});
            me.getEventsPerApp(me.state.apps[0].name);
            me.getActionsPerApp(me.state.apps[0].name);
            me.setState({loading: false});
        })
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    getEventsPerApp(appName){
        var app = this.getAppPerName(appName);
        var me=this;
        var event_list=[];
        var result=me.state.events;
        result.forEach(function(functionObject){
            if(functionObject.event == true && functionObject.func_group == app.module){
                event_list.push(functionObject.func_name);
            }
        });
        
        if(event_list.length > 0){
            //document.getElementById("selectEvent").disabled = false;
            me.setState({selectedEvent: event_list[0]});
        }
        me.setState({eventsPerApp: event_list});
    }

    getActionsPerApp(appName){
        var app = this.getAppPerName(appName);
        var me=this;
        var action_list=[];
        var result=me.state.events;
        result.forEach(function(functionObject){
            if(functionObject.func_group == app.module){
                action_list.push(functionObject.func_name);
            }
        });
        
        if(action_list.length > 0){
            //document.getElementById("selectAction").disabled = false;
            me.setState({selectedAction: action_list[0]});
        }
        me.setState({actionsPerApp: action_list});
    }

    closeModal(){
        this.setState({showModal: false, stepIndex: 1});
        this.reloadModal();
    }

    nextStep(){
        if(this.state.stepIndex < 3){
            this.setState({stepIndex: this.state.stepIndex+1});
        }
    }

    addTrigger(){
        console.log('ADD Trigger Button clicked');
    }

    handleSelectDonorAppChange(){
        var select_element_value=document.getElementById('selectDonorApp').value;
        this.setState({selectedDonorApp: select_element_value});
        this.getEventsPerApp(select_element_value);
    }

    handleSelectEventChange(){
        var select_element_value=document.getElementById('selectEvent').value;
        this.setState({selectedEvent: select_element_value});
    }

    handleSelectReceiverAppChange(){
        var select_element_value=document.getElementById('selectReceiverApp').value;
        this.setState({selectedReceiverApp: select_element_value});
        this.getActionsPerApp(select_element_value);
    }

    handleSelectActionChange(){
        var select_element_value=document.getElementById('selectAction').value;
        this.setState({selectedAction: select_element_value});
    }

    showEventsSelect(){
        var event_options=this.state.eventsPerApp.map(function(event, index){
            return (<option value={event}>{event}</option>);
        });

        if(this.state.eventsPerApp.length==0){
            return(
            <Bootstrap.FormGroup disabled>
                <Bootstrap.ControlLabel disabled>Select event</Bootstrap.ControlLabel>
                <Bootstrap.FormControl id="selectEvent" componentClass="select" placeholder="Select event" onChange={this.handleSelectEventChange.bind(this)} disabled>
                    {event_options}
                </Bootstrap.FormControl>
            </Bootstrap.FormGroup>);
        }
        else{
            return(
            <Bootstrap.FormGroup>
                <Bootstrap.ControlLabel>Select event</Bootstrap.ControlLabel>
                <Bootstrap.FormControl id="selectEvent" componentClass="select" placeholder="Select event" onChange={this.handleSelectEventChange.bind(this)}>
                    {event_options}
                </Bootstrap.FormControl>
            </Bootstrap.FormGroup>);
        }
    }

    showActionsSelect(){
        var action_options=this.state.actionsPerApp.map(function(action, index){
            return (<option value={action}>{action}</option>);
        });

        if(this.state.actionsPerApp.length==0){
            return(
            <Bootstrap.FormGroup disabled>
                <Bootstrap.ControlLabel disabled>Select action</Bootstrap.ControlLabel>
                <Bootstrap.FormControl id="selectAction" componentClass="select" placeholder="Select action" onChange={this.handleSelectActionChange.bind(this)} disabled>
                    {action_options}
                </Bootstrap.FormControl>
            </Bootstrap.FormGroup>);
        }
        else{
            return(
            <Bootstrap.FormGroup>
                <Bootstrap.ControlLabel>Select action</Bootstrap.ControlLabel>
                <Bootstrap.FormControl id="selectAction" componentClass="select" placeholder="Select action" onChange={this.handleSelectActionChange.bind(this)}>
                    {action_options}
                </Bootstrap.FormControl>
            </Bootstrap.FormGroup>);
        }
    }

    showModalButtons(){
        if(this.state.stepIndex == 3){
            return (
                <Bootstrap.ButtonGroup>
                    <Bootstrap.Button bsStyle='primary' onClick={this.addTrigger} style={{marginRight: '5px'}}>
                         Submit
                    </Bootstrap.Button>
                    <Bootstrap.Button onClick={()=> this.closeModal()}>
                        Close
                    </Bootstrap.Button>
                </Bootstrap.ButtonGroup>
            );
        }

        else {
            return (
                <Bootstrap.ButtonGroup>
                    <Bootstrap.Button bsStyle='primary' onClick={this.nextStep} style={{marginRight: '5px'}}>
                        <Bootstrap.Glyphicon glyph='menu-right'></Bootstrap.Glyphicon> Next step</Bootstrap.Button>
                    <Bootstrap.Button onClick={()=> this.closeModal()}>
                        Close
                    </Bootstrap.Button>
                </Bootstrap.ButtonGroup>
            );
        }
    }

    render() {
        var me=this;
        var loading = this.state.loading;
        var app_options=this.state.apps.map(function(app, index){
            return (<option value={app.name}>{app.name}</option>);
        }); 

        return (
                <div>
                    {loading && getSpinner()}
                    <div style={this.props.style} className="card">
                        <div className="card-body">
                            <table className="table striped">
                                <thead>
                                    <tr className="reactable-filterer">
                                        <td>
                                            <h4>Integrations</h4>
                                        </td>
                                        <td style={{textAlign: 'right'}}>                         
                                            <Bootstrap.Button onClick={()=> this.openTriggerModal()}>
                                                <Bootstrap.Glyphicon glyph='plus' />
                                                Create trigger
                                            </Bootstrap.Button>
                                        </td>
                                    </tr>
                                </thead>
                            </table>

                            <Bootstrap.Modal show={this.state.showModal} onHide={this.closeModal}>
                                <Bootstrap.Modal.Header>
                                    <Bootstrap.Modal.Title> Add Trigger</Bootstrap.Modal.Title>
                                </Bootstrap.Modal.Header>
                               
                                <Bootstrap.Modal.Body>
                                    <Bootstrap.Tabs id="tabs" activeKey={this.state.stepIndex}>
                                        
                                        <Bootstrap.Tab eventKey={1} title="Step 1">
                                            
                                            <Bootstrap.FormGroup>
                                                <Bootstrap.ControlLabel>Select Donor app</Bootstrap.ControlLabel>
                                                <Bootstrap.FormControl id="selectDonorApp" componentClass="select" placeholder="Select donor app" onChange={this.handleSelectDonorAppChange.bind(this)}>
                                                    {app_options}
                                                </Bootstrap.FormControl>
                                            </Bootstrap.FormGroup>

                                            {this.showEventsSelect()}
                                        </Bootstrap.Tab>

                                        <Bootstrap.Tab eventKey={2} title="Step 2">
                                             <Bootstrap.FormGroup>
                                                <Bootstrap.ControlLabel>Select Receiver app</Bootstrap.ControlLabel>
                                                <Bootstrap.FormControl id="selectReceiverApp" componentClass="select" placeholder="Select Receiver app" onChange={this.handleSelectReceiverAppChange.bind(this)}>
                                                    {app_options}
                                                </Bootstrap.FormControl>
                                            </Bootstrap.FormGroup>

                                            {this.showActionsSelect()}

                                        </Bootstrap.Tab>
                                        <Bootstrap.Tab eventKey={3} title="Step 3">
                                            <h4>Arguments</h4>
                                            <h4>Action: {this.state.selectedAction}</h4>
                                        </Bootstrap.Tab>
                                    </Bootstrap.Tabs>
                                
                                </Bootstrap.Modal.Body>

                                <Bootstrap.Modal.Footer>
                                    {this.showModalButtons()}
                                </Bootstrap.Modal.Footer>

                            </Bootstrap.Modal>

                            <br/>
                        </div>
                    </div>
                </div>);
}
}

module.exports = connect(state => {
    return { auth: state.auth, alert: state.alert };
})(Integrations);