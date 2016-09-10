var React = require('react');
var Router = require('react-router');
var connect = require('react-redux').connect;

var Login = React.createClass({
    onSubmit: function(e) {
        e.preventDefault();
        var data = JSON.stringify({
            username: this.refs.username.value,
            password: this.refs.password.value
        });

        var dispatch = this.props.dispatch;

        $.ajax({
            type: 'POST',
            url: '/api/login',
            contentType: 'application/json',
            data: data
        }).done(function(data){
            dispatch({type: 'LOGIN', token: data.token});
        }).fail(function(xhr){
            alert(xhr.status);
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
    render: function() {
        return (
            <div className='splash-login'>
            <form className='login-form form-horizontal' onSubmit={this.onSubmit}>
                <div className='form-group'>
                <input placeholder='Username' className='form-control' ref='username'/>
                </div>
                <div className='form-group'>
                <input placeholder='Password' className='form-control' ref='password'/>
                </div>
                <div className='form-group'>
                <button className='btn btn-primary'>Log in</button>
                </div>
            </form>
            </div>
        );
    }
});

module.exports = connect(function(state) {
    return {auth: state.auth};
})(Login);
