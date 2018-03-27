import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';
var Network = require('../network');
import {findDOMNode} from 'react-dom';
import {hashHistory} from 'react-router';

class Store extends Component {
    constructor (props) {
        super(props);
        this.state = {states: []};
        this.getCurrentStates = this.getCurrentStates.bind(this);
        this.launchApp = this.launchApp.bind(this);
        this.openModal = this.openModal.bind(this);
        this.openPanel = this.openPanel.bind(this);
    }

    getCurrentStates () {
        var me = this;
        Network.get('/api/states', this.props.auth.token).done(function (data) {
            me.setState({states: data});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }

    componentDidMount () {
        this.getCurrentStates();
    }

    launchApp (e){
        this.props.dispatch({type: 'LAUNCH', select: e.target.value});
        this.props.dispatch({type: 'OPEN_MODAL'});
        hashHistory.push('/servers');
    }
    openModal () {
        this.props.dispatch({type: 'OPEN_MODAL'});
    }
    openPanel(e){
        var index = e.target.value;
        var state = this.state.states[index];
        hashHistory.push('/panel/' + state.panels[0].key + '/' + state.servers[0]);
    }
    render () {
        var states_rows = this.state.states.map(function(state, index) {
            var description = state.description;
            if(description.length > 106){
                //desc = description.slice(0, 106);
                //desc += '...';
                var popover = (
                    <Bootstrap.Popover id={'popover' + index} title="App description">
                        {description}
                    </Bootstrap.Popover>
                );
                description = (<Bootstrap.OverlayTrigger trigger="click" placement="bottom" overlay={popover}><div>{description}</div></Bootstrap.OverlayTrigger>);
            }
            return (
                <Bootstrap.Col xs={12} sm={6} md={3} key={state.name}>
                    <div className="card card-apps">
                        <div className="card-body">
                            <h4 className="card-title">{state.name}</h4>
                            <div>Version: {state.version}</div>
                            <div className="description ellipsized-text">{description}</div>
                            <Bootstrap.Button bsStyle='primary' onClick={this.launchApp} value={state.name}>
                                Launch
                            </Bootstrap.Button>
                            {'servers' in state && state.servers.length > 0 && <Bootstrap.Button bsStyle='success' onClick={this.openPanel} value={index} style={{float: 'right'}}>
                                Open
                            </Bootstrap.Button>
                            }
                        </div>
                    </div>
                </Bootstrap.Col>
            )
        }.bind(this));

        var NewStateFormRedux = connect(function(state){
            return {auth: state.auth, alert: state.alert, modal: state.modal};
        })(NewStateForm);

        return (
            <div>
                <div className="page-header">
                    <h1 style={{display: 'inline', verticalAlign: 'middle'}}>Available apps</h1>
                    <Bootstrap.Button style={{float: 'right', marginRight: '20px'}} onClick={this.openModal}>
                        <Bootstrap.Glyphicon glyph='plus' />
                        Add app 
                    </Bootstrap.Button>
                </div>
                <div className="container-fluid">
                    <Bootstrap.Row>
                        {states_rows}
                    </Bootstrap.Row>
                </div>
                <NewStateFormRedux getStates = {this.getCurrentStates} />
            </div>
        );
    }
}

class NewStateForm extends Component {
    close() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    }
    render() {
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={() => this.close()}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Add new state</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    <form onSubmit={(e) => this.onSubmit(e)} ref="uploadForm" encType="multipart/form-data" style={{width: '100%', padding: '0 20px'}}>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >App name</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="name" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >Version</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="version" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >Description</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="description" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >Icon</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="icon" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >Dependecy</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="dependency" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >Path</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="path" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >Substates</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='text' ref="substates" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.FormGroup>
                            <Bootstrap.ControlLabel >File</Bootstrap.ControlLabel>
                            <Bootstrap.FormControl type='file' ref="file" />
                        </Bootstrap.FormGroup>
                        <Bootstrap.ButtonGroup>
                            <Bootstrap.Button type="submit" bsStyle='primary'>
                                Create
                            </Bootstrap.Button>
                        </Bootstrap.ButtonGroup>
                    </form>
                </Bootstrap.Modal.Body>
            </Bootstrap.Modal>);

    }
    onSubmit(e) {
        e.preventDefault();
        var str = findDOMNode(this.refs.substates).value.trim();
        str = str.split(/[\s,]+/).join();
        var substates = str.split(",");
        var fd = new FormData();
        fd.append('name', findDOMNode(this.refs.name).value);
        fd.append('version', findDOMNode(this.refs.version).value);
        fd.append('description', findDOMNode(this.refs.description).value);
        fd.append('icon', findDOMNode(this.refs.icon).value);
        fd.append('dependency', findDOMNode(this.refs.dependency).value);
        fd.append('path', findDOMNode(this.refs.path).value);
        fd.append('substates', substates);
        fd.append('file', findDOMNode(this.refs.file).files[0]);
        var me = this;
        Network.post_file('/api/state/add', this.props.auth.token, fd).done(function(data) {
            me.props.getStates();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
}

module.exports = connect(function(state){
    return {auth: state.auth, apps: state.apps, alert: state.alert};
})(Store);
