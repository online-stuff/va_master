import React, { Component } from 'react';
import {Router, Link, IndexLink, hashHistory} from 'react-router';
var Bootstrap = require('react-bootstrap');
import {connect} from 'react-redux';

var Network = require('../network');

const NavLink = (props) => {
    var isActive = window.location.hash.indexOf(props.to) !== -1;
    var className = isActive ? 'active' : '';
    if(isActive){
        var activeKey = -1;
        if('activeKey' in props){ //this.props.to.indexOf('panel') > -1
            activeKey = props.activeKey;
        }
        window.localStorage.setItem('activeKey', activeKey);
    }
    if('tabs' in props){
        return (
            <Link to={props.to} className={className} activeClassName='active' onClick={props.show_tabs.bind(null, props.tabs)}>
                {props.children}
            </Link>
        );
    }
    if('tab' in props){
        return (
            <Link to={props.to} className={className} activeClassName='active'>
                {props.children}
            </Link>
        );
    }

    return (
        <Link to={props.to} className={className} activeClassName='active' onClick={props.reset_tabs}>
            {props.children}
        </Link>
    );
}

class Home extends Component {
    constructor (props) {
        super(props);
        var activeKey = window.localStorage.getItem('activeKey');
        if(activeKey){
            activeKey = parseInt(activeKey);
        }else{
            activeKey = -1;
        }
        this.state = {
            'data': [],
            'collapse': false,
            'activeKey': activeKey,
            'stats': {}
        };
        this.show_tabs = this.show_tabs.bind(this);
        this.reset_tabs = this.reset_tabs.bind(this);
        this.getPanels = this.getPanels.bind(this);
        this.navbar_click = this.navbar_click.bind(this);
        this.handleAlertDismiss = this.handleAlertDismiss.bind(this);
        this.collapse = this.collapse.bind(this);
    }
    show_tabs(key){
        this.props.dispatch({type: 'SHOW_TABS', key: key});
    }
    reset_tabs(){
        this.props.menu.showTabs && this.props.dispatch({type: 'RESET_TABS'});
    }
    getPanels() {
        var me = this;
        Network.get('/api/panels', this.props.auth.token).done(function (data) {
            me.setState({data: data});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
    getStats() {
        var me = this;
        Network.get('/api/panels/stats', this.props.auth.token).done(function (data) {
            me.setState({stats: data});
        }).fail(function (msg) {
            me.props.dispatch({type: 'SHOW_ALERT', msg: msg});
        });
    }
    componentDidMount() {
        if(!this.props.auth.token){
            hashHistory.push('/login');
        }else{
            this.getPanels();
            this.getStats();
        }
    }
    componentWillReceiveProps(props) {
        if(!props.auth.token) {
            hashHistory.push('/login');
        }
        var activeKey = window.localStorage.getItem('activeKey') || -1;
        if(this.state.activeKey != activeKey){
            this.setState({activeKey: parseInt(activeKey)});
        }
    }
    navbar_click(key, event) {
        if(key === 'logout')
            this.props.dispatch({type: 'LOGOUT'});
        else if(key === 'users'){
            this.reset_tabs();
            this.props.dispatch({type: 'SHOW_TABS', key: 'users'});
            hashHistory.push('/users_users');
        }
    }
    collapse() {
        this.setState({collapse: !this.state.collapse});
        var me = this;
        setTimeout(function(){
            me.props.dispatch({type: 'COLLAPSE'});
        }, 300);
    }
    handleAlertDismiss() {
        this.props.dispatch({type: 'HIDE_ALERT'});
    }
    render() {
        var me = this;
        var panels = this.state.data.filter(function(panel) {
            if(panel.servers.length > 0){
                return true;
            }
            return false;
        }).map(function(panel, i) {
            var header = (
                <span><i className={'fa ' + panel.icon} /> {panel.name} <i className='fa fa-angle-down pull-right' /></span>
            )
            var servers = panel.servers.map((server) => {
                var subpanels = panel.panels.map((panel) => {
                    return (
                        <li key={panel.key}><NavLink to={'panel/' + panel.key + '/' + server} activeKey={i} reset_tabs={me.reset_tabs}>
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
        var key = this.props.menu.showTabs || window.location.hash.split('_')[0].slice(2);
        var menu_tabs = key in this.props.menu.tabs ? this.props.menu.tabs[key] : [];
        var tabs = menu_tabs.map(function(tab){
            return <li key={tab.title}><NavLink to={tab.link} tab>{tab.title}</NavLink></li>
        });
        /*var navLinks = [{to: 'providers', glyph: 'hdd'}, {to: 'servers', klasa: 'server'}, 
            {to: 'store', glyph: 'th'}, {to: 'services', glyph: 'cloud'},
            {to: 'servers', klasa: 'server'}, {to: 'servers', klasa: 'server'}
        ];*/

        return (
            <div id="app-content">
                <Bootstrap.Navbar bsStyle='inverse'>
                    <Bootstrap.Navbar.Header>
                        <Bootstrap.Glyphicon glyph='menu-hamburger' onClick={this.collapse} />
                        <img src='/static/logo.png' className='top-logo'/>
                        <Bootstrap.Navbar.Toggle />
                    </Bootstrap.Navbar.Header>
                    <Bootstrap.Navbar.Collapse>
                        {tabs.length > 0 && <Bootstrap.Nav>
                            {tabs}
                        </Bootstrap.Nav>}
                        <Bootstrap.Nav pullRight>
                            <Bootstrap.NavDropdown title={this.props.auth.username} onSelect={this.navbar_click} id="nav-dropdown" pullRight>
                                    <Bootstrap.MenuItem eventKey='users'>Users</Bootstrap.MenuItem>
                                    <li role="presentation"><a role="menuitem" href="https://github.com/VapourApps/va_master/tree/master/docs" target="_blank">Help</a></li>
                                    <Bootstrap.MenuItem eventKey='logout'>Logout</Bootstrap.MenuItem>
                            </Bootstrap.NavDropdown>
                        </Bootstrap.Nav>
                    </Bootstrap.Navbar.Collapse>
                </Bootstrap.Navbar>
                <div className='main-content'>
                    <div className='sidebar' style={this.state.collapse?{display: 'none'}:{display: 'flex'}}>
                        <ul className='left-menu'>
                            <li>
                            <IndexLink to='' activeClassName='active' onClick={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='home' /> Overview</IndexLink>
                            </li>
                            <li>
                            <NavLink to='providers' reset_tabs={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='hdd' /> Providers <span className="badge">{this.state.stats.providers}</span></NavLink>
                            </li>
                            <NavLink to='servers' reset_tabs={this.reset_tabs}>
                                <span><i className='fa fa-server' /> Servers <span className="badge">{this.state.stats.servers}</span></span>
                            </NavLink>
                            <li>
                            <NavLink to='store' reset_tabs={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='th' /> Apps <span className="badge">{this.state.stats.apps}</span></NavLink>
                            </li>
                            <li>
                            <NavLink to='services' reset_tabs={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='cloud' /> Services <span className="badge">{this.state.stats.services}</span></NavLink>
                            </li>
                            <li>
                            <NavLink to='vpn_status' tabs='vpn' show_tabs={this.show_tabs}>
                                <span><i className='fa fa-lock' /> VPN <span className="badge">{this.state.stats.vpn}</span></span>
                            </NavLink>
                            <NavLink to='log' reset_tabs={this.reset_tabs}>
                                <span><i className='fa fa-bar-chart' /> Log</span>
                            </NavLink>
                            <NavLink to='billing' reset_tabs={this.reset_tabs}>
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
                    <div className="page-content">
                        {this.props.children}
                    </div>
                    {this.props.alert.show && React.createElement(Bootstrap.Alert, {bsStyle: this.props.alert.className, onDismiss: this.handleAlertDismiss, className: "messages"}, this.props.alert.msg) }
                </div>
				<div className="footer">
					Powered by <a href="//vapour-apps.com" target="_blank">VapourApps</a> | <a href="mailto:support@vapour-apps.com">support@vapour-apps.com</a>
				</div>
            </div>
        );
    }
}

module.exports = connect(function(state) {
    return {auth: state.auth, alert: state.alert, menu: state.menu}
})(Home);

