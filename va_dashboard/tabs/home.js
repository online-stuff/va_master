var React = require('react');
var Router = require('react-router');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;

var Network = require('../network');

var Home = React.createClass({
    getInitialState: function() {
        return {
            'panels': []
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
    render: function () {
        var panels = this.state.panels.map(function(panel, i) {
            var header = (
                <span><i className={'fa fa-' + panel.icon} /> {panel.name} <i className='fa fa-angle-down pull-right' /></span>
            )
            var instances = panel.instances.map(function(instance) {
                var subpanels = panel.subpanels.map(function(panel) {
                    return (
                        <li key={panel.key}><Router.Link to={'panel/' + panel.key + '/' + instance} activeClassName='active'>
                            <span>{panel.name}</span>
                        </Router.Link></li>
                    );
                });
                return (
                    <div key={instance}>
                        <span className="panels-title">{instance}</span>
                        <ul className='left-menu'>
                            {subpanels}
                        </ul>
                    </div>
                );
            });
            return (
                <Bootstrap.Panel key={panel.name} header={header} eventKey={i}>
                    {instances}
                </Bootstrap.Panel>
            );
        });

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
                    <Bootstrap.Glyphicon glyph='cloud' /> Store</Router.Link>
                    </li>
                    <li>
                    <Router.Link to='vpn' activeClassName='active'>
                        <span><i className='fa fa-lock' /> VPN</span>
                    </Router.Link>
                    </li>
                    <li role="separator" className="divider-vertical"></li>
                    <li className="panels-title">Admin panels</li>
                    <li><Bootstrap.Accordion>
                        {panels}
                    </Bootstrap.Accordion></li>
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
