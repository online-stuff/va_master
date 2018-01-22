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
            'activeKey': activeKey
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
    componentDidMount() {
        if(!this.props.auth.token){
            hashHistory.push('/login');
        }else{
            this.getPanels();
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
            <div>
                <Bootstrap.Navbar bsStyle='inverse'>
                    <Bootstrap.Navbar.Header>
                        <Bootstrap.Glyphicon glyph='menu-hamburger' onClick={this.collapse} />
                        <img src='/static/logo.png' className='top-logo'/>
                    </Bootstrap.Navbar.Header>
                    <Bootstrap.Navbar.Collapse>
                        <Bootstrap.Nav>
                            {tabs}
                        </Bootstrap.Nav>
                        <Bootstrap.Nav pullRight>
                            <Bootstrap.NavDropdown title={this.props.auth.username} onSelect={this.navbar_click} id="nav-dropdown" pullRight>
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
                            <IndexLink to='' activeClassName='active' onClick={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='home' /> Overview</IndexLink>
                            </li>
                            <li>
                            <NavLink to='providers' reset_tabs={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='hdd' /> Providers</NavLink>
                            </li>
                            <NavLink to='servers' reset_tabs={this.reset_tabs}>
                                <span><i className='fa fa-server' /> Servers</span>
                            </NavLink>
                            <li>
                            <NavLink to='store' reset_tabs={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='th' /> Apps</NavLink>
                            </li>
                            <li>
                            <NavLink to='services' reset_tabs={this.reset_tabs}>
                                <Bootstrap.Glyphicon glyph='cloud' /> Services</NavLink>
                            </li>
                            <li>
                            <NavLink to='vpn_status' tabs='vpn' show_tabs={this.show_tabs}>
                                <span><i className='fa fa-lock' /> VPN</span>
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
                    <div className="page-content" style={this.state.collapse?{'left': '0', 'width': '96.4vw'}:{'left': '15.4vw', 'width': '81vw'}}>
                        {this.props.children}
                    </div>
                    {this.props.alert.show && React.createElement(Bootstrap.Alert, {bsStyle: 'danger', onDismiss: this.handleAlertDismiss, className: "messages"}, this.props.alert.msg) }
                </div>
            </div>
        );
    }
}

Home = connect(function(state) {
    return {auth: state.auth, alert: state.alert, menu: state.menu}
})(Home);

module.exports = Home;
