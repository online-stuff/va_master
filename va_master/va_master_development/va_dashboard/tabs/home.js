var React = require('react');
var Router = require('react-router');
var Bootstrap = require('react-bootstrap');
var connect = require('react-redux').connect;

var Network = require('../network');

var NavLink = React.createClass({

    render: function () {
        var isActive = window.location.hash.indexOf(this.props.to) !== -1;
        var className = isActive ? 'active' : '';
        if(isActive){
            var activeKey = -1;
            if('activeKey' in this.props){ //this.props.to.indexOf('panel') > -1
                activeKey = this.props.activeKey;
            }
            window.localStorage.setItem('activeKey', activeKey);
        }

        return (
            <Router.Link to={this.props.to} className={className} activeClassName='active'>
                {this.props.children}
            </Router.Link>
        );
    }
});

var Home = React.createClass({
    getInitialState: function() {
        var activeKey = window.localStorage.getItem('activeKey');
        if(activeKey){
            activeKey = parseInt(activeKey);
        }else{
            activeKey = -1;
        }
        return {
            'data': [],
            'collapse': false,
            'activeKey': activeKey
        };
    },
    getPanels: function() {
        var me = this;
        Network.get('/api/panels', this.props.auth.token).done(function (data) {
            me.setState({data: data});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
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
        var activeKey = window.localStorage.getItem('activeKey') || -1;
        if(this.state.activeKey != activeKey){
            this.setState({activeKey: parseInt(activeKey)});
        }
    },
    navbar_click: function (key, event) {
        if(key === 'logout')
            this.props.dispatch({type: 'LOGOUT'});
        else if(key === 'users')
            Router.hashHistory.push('/users');
    },
    collapse: function () {
        this.setState({collapse: !this.state.collapse});
        var me = this;
        setTimeout(function(){
            me.props.dispatch({type: 'COLLAPSE'});
        }, 300);
    },
    handleAlertDismiss() {
        this.props.dispatch({type: 'HIDE_ALERT'});
    },
    render: function () {
        var panels = this.state.data.filter(function(panel) {
            if(panel.servers.length > 0){
                return true;
            }
            return false;
        }).map(function(panel, i) {
            var header = (
                <span><i className={'fa ' + panel.icon} /> {panel.name} <i className='fa fa-angle-down pull-right' /></span>
            )
            var servers = panel.servers.map(function(server) {
                var subpanels = panel.panels.map(function(panel) {
                    return (
                        <li key={panel.key}><NavLink to={'panel/' + panel.key + '/' + server} activeKey={i}>
                            <span>{panel.name}</span>
                        </NavLink></li>
                    );
                });
                return (
                    <div key={server}>
                        <span className="panels-title">{server}</span>
                        <ul className='left-menu'>
                            {subpanels}
                        </ul>
                    </div>
                );
            });
            return (
                <Bootstrap.Panel key={panel.name} header={header} eventKey={i}>
                    {servers}
                </Bootstrap.Panel>
            );
        });

        return (
        <div>
            <Bootstrap.Navbar bsStyle='inverse'>
                <Bootstrap.Navbar.Header>
                    <Bootstrap.Glyphicon glyph='menu-hamburger' onClick={this.collapse} />
                    <img src='/static/logo.png' className='top-logo'/>
                </Bootstrap.Navbar.Header>
                <Bootstrap.Navbar.Collapse>
                    <Bootstrap.Nav pullRight={true}>
                        <Bootstrap.NavDropdown title={this.props.auth.username} onSelect={this.navbar_click} id="nav-dropdown">
                                <Bootstrap.MenuItem eventKey='users'>Users</Bootstrap.MenuItem>
                                <Bootstrap.MenuItem eventKey='logout'>Logout</Bootstrap.MenuItem>
                        </Bootstrap.NavDropdown>
                    </Bootstrap.Nav>
                </Bootstrap.Navbar.Collapse>
            </Bootstrap.Navbar>
            <div className='main-content'>
                <div className='sidebar' style={this.state.collapse?{left: '-15.4vw'}:{left: 0}}>
                    <ul className='left-menu'>
                        <li>
                        <Router.IndexLink to='' activeClassName='active'>
                            <Bootstrap.Glyphicon glyph='home' /> Overview</Router.IndexLink>
                        </li>
                        <li>
                        <NavLink to='providers'>
                            <Bootstrap.Glyphicon glyph='hdd' /> Providers</NavLink>
                        </li>
                        <NavLink to='servers'>
                            <span><i className='fa fa-server' /> Servers</span>
                        </NavLink>
                        <li>
                        <NavLink to='store'>
                            <Bootstrap.Glyphicon glyph='th' /> Apps</NavLink>
                        </li>
                        <li>
                        <NavLink to='services'>
                            <Bootstrap.Glyphicon glyph='cloud' /> Services</NavLink>
                        </li>
                        <li>
                        <NavLink to='vpn'>
                            <span><i className='fa fa-lock' /> VPN</span>
                        </NavLink>
                        <NavLink to='log'>
                            <span><i className='fa fa-bar-chart' /> Log</span>
                        </NavLink>
                        <NavLink to='billing'>
                            <span><i className='fa fa-credit-card' /> Billing</span>
                        </NavLink>
                        </li>
                        <li role="separator" className="divider-vertical"></li>
                        <li className="panels-title">Admin panels</li>
                        <li>
                            <Bootstrap.Accordion key={this.state.activeKey} defaultActiveKey={this.state.activeKey}>
                                {panels}
                            </Bootstrap.Accordion>
                        </li>
                    </ul>
                </div>
                <div className="page-content" style={this.state.collapse?{'left': '0', 'width': '97.4vw'}:{'left': '15.4vw', 'width': '82vw'}}>
                    {this.props.children}
                </div>
                {this.props.alert.show && React.createElement(Bootstrap.Alert, {bsStyle: 'danger', onDismiss: this.handleAlertDismiss, className: "messages"}, this.props.alert.msg) }
            </div>
        </div>
        );
    }
});

Home = connect(function(state) {
    return {auth: state.auth, alert: state.alert}
})(Home);

module.exports = Home;
