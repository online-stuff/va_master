var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');
var Router = require('react-router');

var Store = React.createClass({
    getInitialState: function () {
        return {states: []};
    },

    getCurrentStates: function () {
        var me = this;
        Network.get('/api/states', this.props.auth.token).done(function (data) {
            me.setState({states: data});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    },

    componentDidMount: function () {
        this.getCurrentStates();
    },

    launchApp: function (e){
        this.props.dispatch({type: 'LAUNCH', select: e.target.value});
        this.props.dispatch({type: 'OPEN_MODAL'});
        Router.hashHistory.push('/servers');
    },
    openModal: function () {
        this.props.dispatch({type: 'OPEN_MODAL'});
    },
    openPanel: function(e){
        var index = e.target.value;
        var state = this.state.states[index];
        Router.hashHistory.push('/panel/' + state.panels[0].key + '/' + state.servers[0]);
    },
    render: function () {
        var states_rows = this.state.states.map(function(state, index) {
            var description = state.description;
            if(description.length > 106){
                //desc = description.slice(0, 106);
                //desc += '...';
                popover = (
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
});

var NewStateForm = React.createClass({
    close: function() {
        this.props.dispatch({type: 'CLOSE_MODAL'});
    },
    render: function () {
        return (
            <Bootstrap.Modal show={this.props.modal.isOpen} onHide={this.close}>
                <Bootstrap.Modal.Header closeButton>
                  <Bootstrap.Modal.Title>Add new state</Bootstrap.Modal.Title>
                </Bootstrap.Modal.Header>

                <Bootstrap.Modal.Body>
                    <form onSubmit={this.onSubmit} ref="uploadForm" encType="multipart/form-data" style={{width: '100%', padding: '0 20px'}}>
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

    },
    onSubmit: function(e) {
        e.preventDefault();
        var str = ReactDOM.findDOMNode(this.refs.substates).value.trim();
        str = str.split(/[\s,]+/).join();
        var substates = str.split(",");
        var fd = new FormData();
        fd.append('name', ReactDOM.findDOMNode(this.refs.name).value);
        fd.append('version', ReactDOM.findDOMNode(this.refs.version).value);
        fd.append('description', ReactDOM.findDOMNode(this.refs.description).value);
        fd.append('icon', ReactDOM.findDOMNode(this.refs.icon).value);
        fd.append('dependency', ReactDOM.findDOMNode(this.refs.dependency).value);
        fd.append('path', ReactDOM.findDOMNode(this.refs.path).value);
        fd.append('substates', substates);
        fd.append('file', ReactDOM.findDOMNode(this.refs.file).files[0]);
        var me = this;
        Network.post_file('/api/state/add', this.props.auth.token, fd).done(function(data) {
            me.props.getStates();
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
});

Store = connect(function(state){
    return {auth: state.auth, apps: state.apps, alert: state.alert};
})(Store);

module.exports = Store;
