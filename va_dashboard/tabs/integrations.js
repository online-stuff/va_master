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
            selectedDonorApp: '',
            selectedEvent: ''
        };
        this.openTriggerModal=this.openTriggerModal.bind(this);
        this.closeModal=this.closeModal.bind(this);
        this.nextStep=this.nextStep.bind(this);
        this.addTrigger=this.addTrigger.bind(this);
        this.showModalButtons=this.showModalButtons.bind(this);
        this.getApps=this.getApps.bind(this);
        this.getEventsPerApp=this.getEventsPerApp.bind(this);
    }

    componentDidMount() {
        var me=this;
        me.setState({loading: false});
        this.getApps();
    }

    openTriggerModal(){
        this.setState({showModal: true});
    }

    getApps(){
        var me=this;
        console.log('Calling get apps');
        Network.get('/api/states', this.props.auth.token)
        .done(function (data){
            var result = data;
            console.log('Result', result);
            var app_list=[];
            result.forEach(function(appObject){
                app_list.push(appObject.name);
            });
            if(app_list.length > 0){
                console.log('Default Element(App): ', app_list[0]);
                me.getEventsPerApp(app_list[0]);
                me.setState({selectedDonorApp: app_list[0]});
            }
            me.setState({apps: app_list});
            console.log('App list', app_list);
        })
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    getEventsPerApp(appName){
        var me=this;
        Network.get('/api/panels/get_functions', this.props.auth.token)
        .done(function (data){
            var result = data;
            console.log('Result (Get events per app):', result);
            var event_list=[];
            result.forEach(function(functionObject){
                if(functionObject.event == true && functionObject.func_group == appName){
                    event_list.push(functionObject.func_name);
                }
            });
            if(event_list.length > 0){
                document.getElementById("selectEvent").disabled = false;
                console.log('Default Element (Event): ', event_list[0]);
                me.setState({selectedEvent: event_list[0]});
            }
            else{
                document.getElementById("selectEvent").disabled = true;
            }
            me.setState({events: event_list});
            console.log('Event list', event_list);
        })
        .fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    closeModal(){
        this.setState({showModal: false, stepIndex: 1});
    }

    nextStep(){
        console.log(this.state.stepIndex);
        if(this.state.stepIndex < 3){
            this.setState({stepIndex: this.state.stepIndex+1});
        }
    }

    addTrigger(){
        console.log('ADD Trigger Button clicked');
    }

    handleSelectDonorAppChange(){
        var select_element_value=document.getElementById('selectDonorApp').value;
        console.log('App change: ', select_element_value);
        this.setState({selectedDonorApp: select_element_value});
        this.getEventsPerApp(select_element_value);
    }

    handleSelectEventChange(){
        var select_element_value=document.getElementById('selectEvent').value;
        console.log('Event change: ', select_element_value);
        this.setState({selectedEvent: select_element_value});
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
            return (<option value={app}>{app}</option>);
        }); 

        var event_options=this.state.events.map(function(event, index){
            return (<option value={event}>{event}</option>);
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

                            <Bootstrap.Modal show={this.state.showModal} onHide={this.closeModal} closeButton>
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

                                            <Bootstrap.FormGroup>
                                                <Bootstrap.ControlLabel>Select event</Bootstrap.ControlLabel>
                                                <Bootstrap.FormControl id="selectEvent" componentClass="select" placeholder="Select event" onChange={this.handleSelectEventChange.bind(this)}>
                                                    {event_options}
                                                </Bootstrap.FormControl>
                                            </Bootstrap.FormGroup>
                                        </Bootstrap.Tab>

                                        <Bootstrap.Tab eventKey={2} title="Step 2">
                                            <h4>Choose App2</h4>
                                        </Bootstrap.Tab>
                                        <Bootstrap.Tab eventKey={3} title="Step 3">
                                            <h4>Arguments</h4>
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