var React = require('react');
var Router = require('react-router');
var Bootstrap = require('react-bootstrap');
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
    logOut: function (key, event) {
        if(key === 'logout')
        this.props.dispatch({type: 'LOGOUT'});
    },
    render: function () {
        return (
        <div>
            <Bootstrap.Navbar bsStyle='inverse'>
                <Bootstrap.Navbar.Header>
                    <Bootstrap.Navbar.Brand><img src='/static/logo.png' className='top-logo'/></Bootstrap.Navbar.Brand>
                </Bootstrap.Navbar.Header>
                <Bootstrap.Navbar.Collapse>
                    <Bootstrap.Nav pullRight={true}>
                        <Bootstrap.NavDropdown title={this.props.auth.username} onSelect={this.logOut}>
                                <Bootstrap.MenuItem eventKey='logout'>Logout</Bootstrap.MenuItem>
                        </Bootstrap.NavDropdown>
                    </Bootstrap.Nav>
                </Bootstrap.Navbar.Collapse>
            </Bootstrap.Navbar>
            <div className='sidebar'>
                <ul className='left-menu'>
                    <li>
                    <Router.IndexLink to='' activeClassName='active'>
                    <Bootstrap.Glyphicon glyph='home' /> Overview</Router.IndexLink>
                    </li>
                    <li>
                    <Router.Link to='hosts' activeClassName='active'>
                    <Bootstrap.Glyphicon glyph='hdd' /> Hosts</Router.Link>
                    </li>
                    <li>
                    <Router.Link to='apps' activeClassName='active'>
                    <Bootstrap.Glyphicon glyph='th' /> Apps</Router.Link>
                    </li>
                    <li>
                    <Router.Link to='store' activeClassName='active'>
                    <Bootstrap.Glyphicon glyph='th' /> Store</Router.Link>
                    </li>
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
