var React = require('react');
var Bootstrap = require('react-bootstrap');
var Router = require('react-router');
var connect = require('react-redux').connect;
var Network = require('./network');

var Login = React.createClass({
    onSubmit: function(e) {
        e.preventDefault();
        var data = {
            username: this.state.username,
            password: this.state.password
        };

        var me = this;
        me.props.dispatch({type: 'LOGIN_START'});
        Network.post('/api/login', null, data).done(function(d) {
            setTimeout(function () {
                me.props.dispatch({type: 'LOGIN_GOOD', token: d.token,
                    username: data.username});
            }, 300);
        }).fail(function(xhr) {
            setTimeout(function () {
                me.props.dispatch({type: 'LOGIN_ERROR'});
            }, 300);
        });
    },
    componentWillReceiveProps: function(props) {
        if(props.auth.token){
            Router.hashHistory.push('/');
        }
    },
    componentDidMount: function () {
        document.body.className = 'login';
    },
    componentWillUnmount: function () {
        document.body.className = '';
    },
    getInitialState: function () {
        return {username: '', password: ''};
    },
    render: function() {
        let status = null;
        if(this.props.auth.inProgress) {
            status = (<Bootstrap.Alert bsStyle='info'>Logging in...</Bootstrap.Alert>);
        }
        if(this.props.auth.loginError) {
            status = (<Bootstrap.Alert bsStyle='danger'>Failed logging in.</Bootstrap.Alert>);
        }

        return (
            <div className='splash-login'>
            <form className='login-form form-horizontal' onSubmit={this.onSubmit}>
                <img src='/static/logo-splash.png' alt='VapourApps' className='splash-logo'/>
                <Bootstrap.FormGroup controlId='username'>
                    <Bootstrap.ControlLabel>Username</Bootstrap.ControlLabel>
                    <Bootstrap.FormControl type='text' placeholder='Enter username...'
                      name='username' onChange={this.onInput} value={this.state.username}/>
                </Bootstrap.FormGroup>

                <Bootstrap.FormGroup controlId='username'>
                    <Bootstrap.ControlLabel>Password</Bootstrap.ControlLabel>
                    <Bootstrap.FormControl placeholder='Enter password...' type='password'
                      name='password' onChange={this.onInput} value={this.state.password} />
                </Bootstrap.FormGroup>

                <Bootstrap.FormGroup>
                    <Bootstrap.Button bsStyle='primary' type='submit'>Log in</Bootstrap.Button>
                </Bootstrap.FormGroup>
            </form>
            {status}
            </div>
        );
    },
    onInput: function (e) {
        if(e.target.name === 'username') {
            this.setState({username: e.target.value});
        } else {
            this.setState({password: e.target.value});
        }
    }
});

module.exports = connect(function(state) {
    return {auth: state.auth};
})(Login);
