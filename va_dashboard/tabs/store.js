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
        });
    },

    componentDidMount: function () {
        this.getCurrentStates();
    },

    launchApp: function (e){
        this.props.dispatch({type: 'LAUNCH', select: e.target.value});
        Router.hashHistory.push('/apps');
    },

    render: function () {
        var states_rows = this.state.states.map(function(state) {
            return (
                <Bootstrap.Col xs={12} sm={6} md={3} key={state.name} className="tile">
                    <div className="title">{state.name}</div>
                    <div>Version: {state.version}</div>
                    <div className="description">{state.description}</div>
                    <Bootstrap.Button bsStyle='primary' onClick={this.launchApp} value={state.name}>
                        Launch
                    </Bootstrap.Button>
                </Bootstrap.Col>
            )
        }.bind(this));

        var NewStateFormRedux = connect(function(state){
            return {auth: state.auth};
        })(NewStateForm);

        return (
            <div>
                <Bootstrap.PageHeader>Current states</Bootstrap.PageHeader>
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
    render: function () {
        return (
            <div>
                <Bootstrap.PageHeader>Add new state</Bootstrap.PageHeader>
                <form onSubmit={this.onSubmit} ref="uploadForm" encType="multipart/form-data">
                    <Bootstrap.FormGroup>
                        <Bootstrap.ControlLabel >State name</Bootstrap.ControlLabel>
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
            </div>
        );

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
        });
    }
});

Store = connect(function(state){
    return {auth: state.auth, apps: state.apps};
})(Store);

module.exports = Store;
