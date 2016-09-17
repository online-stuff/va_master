var React = require('react');
var Router = require('react-router');
var connect = require('react-redux').connect;

var Network = require('../network');

var Home = React.createClass({
    componentDidMount: function() {
        if(!this.props.auth.token){
            Router.hashHistory.push('/login');
        }
    },
    componentWillReceiveProps: function(props) {
        if(!props.auth.token) {
            Router.hashHistory.push('/login');
        }
    },
    logOut: function () {
        this.props.dispatch({type: 'LOGOUT'});
    },
    render: function () {
        return (
        <div>
            <div className='top-header'>
                <img src='/static/logo.png' className='logo' style={{float: 'left'}}/>
                <button className='btn btn-default logout' onClick={this.logOut}>Logout ({this.props.auth.username})</button>
                <div className='clearfix' />
            </div>
            <div className='sidebar'>
                <ul className='left-menu'>
                    <li><Router.IndexLink to='' activeClassName='active'>Overview</Router.IndexLink></li>
                    <li><Router.Link to='hosts' activeClassName='active'>Hosts</Router.Link></li>
                    <li><Router.Link to='apps' activeClassName='active'>Apps</Router.Link></li>
                </ul>
            </div>
            <div className='main-content'>
                {this.props.children}
            </div>
        </div>
        );
    }
});

Home = connect(function(state) {
    return {auth: state.auth}
})(Home);

module.exports = Home;
