import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');
var classNames = require('classnames');
import { connect } from 'react-redux';
var Network = require('../network');
import {Table, Tr, Td} from 'reactable';
import { getSpinner } from './util';

class UsersPermissions extends Component {
    constructor(props) {
        super(props);
        this.state = {
            loading: true,
            permUser: {}
        };
    }

    componentDidMount() {
        this.setState({loading: false, permUser: this.props.user});
    }

    render() {
        var me=this;
        var loading = this.state.loading;
       
        return (
                <div>
                    {loading && getSpinner()}
                    <div style={this.props.style} className="card">
                        <div className="card-body">
                            <h2>User Permissions</h2>
                            <p>{JSON.stringify(this.state.permUser)}</p>
                        </div>
                    </div>
                </div>);
}
}

module.exports = connect(state => {
    return { auth: state.auth, alert: state.alert, user: state.permissions.permUser};
})(UsersPermissions);