var React = require('react');
var Router = require('react-router');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;

var Network = require('../network');

var Home = React.createClass({
    getInitialState: function() {
        return {
            'panels': [],
            'collapse': false
        };
    },
    getPanels: function() {
        var me = this;
        Network.get('/api/panels', this.props.auth.token).done(function (data) {
            me.setState({panels: data.panels});
        });
    },
    componentDidMount: function() {
        if(!this.props.auth.token){
            Router.hashHistory.push('/login');
        }else{
            this.getPanels();
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
    collapse: function () {
        this.setState({collapse: !this.state.collapse});
    },
    render: function () {

        return (
        <div>
            <Bootstrap.Navbar bsStyle='inverse'>
                <Bootstrap.Navbar.Header>
                    <Bootstrap.Glyphicon glyph='menu-hamburger' onClick={this.collapse} />
                    <img src='/static/logo.png' className='top-logo'/>
                </Bootstrap.Navbar.Header>
                <Bootstrap.Navbar.Collapse>
                    <Bootstrap.Nav pullRight={true}>
                        <Bootstrap.NavDropdown title={this.props.auth.username} onSelect={this.logOut} id="nav-dropdown">
                                <Bootstrap.MenuItem eventKey='logout'>Logout</Bootstrap.MenuItem>
                        </Bootstrap.NavDropdown>
                    </Bootstrap.Nav>
                </Bootstrap.Navbar.Collapse>
            </Bootstrap.Navbar>
            <div className='main-content'>
                <div className='sidebar' style={this.state.collapse?{left: -210}:{left: 0}}>
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
                        <Bootstrap.Glyphicon glyph='cloud' /> Store</Router.Link>
                        </li>
                        <li>
                        <Router.Link to='vpn' activeClassName='active'>
                            <span><i className='fa fa-lock' /> VPN</span>
                        </Router.Link>
                        </li>
                    </ul>
                </div>
                <div className="page-content" style={this.state.collapse?{'left': '15px', 'width': '95vw'}:{'left': '230px', 'width': '80vw'}}>
                    {this.props.children}
                </div>
            </div>
        </div>
        );
    }
});

Home = connect(function(state) {
    return {auth: state.auth}
})(Home);

module.exports = Home;
