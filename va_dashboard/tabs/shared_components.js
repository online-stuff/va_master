import React, { Component } from 'react';
var Bootstrap = require('react-bootstrap');

const ConfirmPopup = (props) => {
    return (
        <Bootstrap.Modal show={props.show} onHide={props.close}>
            <Bootstrap.Modal.Header closeButton>
                <Bootstrap.Modal.Title>Confirm action</Bootstrap.Modal.Title>
            </Bootstrap.Modal.Header>

            <Bootstrap.Modal.Body>
                <p>{props.body}</p>
            </Bootstrap.Modal.Body>

            <Bootstrap.Modal.Footer>
                <Bootstrap.Button onClick={props.close}>Cancel</Bootstrap.Button>
                <Bootstrap.Button onClick={props.action.bind(null, ...props.data)} bsStyle = "primary">Confirm</Bootstrap.Button>
            </Bootstrap.Modal.Footer>
        </Bootstrap.Modal>
    );
}


module.exports = {
    ConfirmPopup,
};
