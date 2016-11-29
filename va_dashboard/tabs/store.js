var React = require('react');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;
var Network = require('../network');
var ReactDOM = require('react-dom');

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

    render: function () {
        var states_rows = this.state.states.map(function(state) {
            return (
                <tr key={state.Name}>
                    <td>{state.Name}</td>
                    <td>{state.Description}</td>
                </tr>
            )
        });

        var NewStateFormRedux = connect(function(state){
            return {auth: state.auth};
        })(NewStateForm);

        return (
            <div>
                <NewStateFormRedux getStates = {this.getCurrentStates} />
                <Bootstrap.PageHeader>Current states</Bootstrap.PageHeader>
                <Bootstrap.Table striped bordered hover>
                    <thead>
                        <tr>
                        <td>State name</td>
                        <td>Description</td>
                        </tr>
                    </thead>
                    <tbody>
                        {states_rows}
                    </tbody>
                </Bootstrap.Table>
            </div>
        );
    }
});

var NewStateForm = React.createClass({
    render: function () {
        return (
            <div>
                <Bootstrap.PageHeader>Add new state</Bootstrap.PageHeader>
                <form onSubmit={this.onSubmit}>
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
        var data = {
            name: ReactDOM.findDOMNode(this.refs.name).value,
            version: ReactDOM.findDOMNode(this.refs.version).value,
            description: ReactDOM.findDOMNode(this.refs.description).value,
            icon: ReactDOM.findDOMNode(this.refs.icon).value,
            dependency: ReactDOM.findDOMNode(this.refs.dependency).value,
            path: ReactDOM.findDOMNode(this.refs.path).value
        };
        var me = this;
        Network.post('/api/state/add', this.props.auth.token, data).done(function(data) {
            me.props.getStates();
        });
    }
});

Store = connect(function(state){
    return {auth: state.auth};
})(Store);

module.exports = Store;
