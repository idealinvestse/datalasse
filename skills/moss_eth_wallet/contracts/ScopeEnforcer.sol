// SPDX-License-Identifier: MIT
pragma solidity ^0.8.27;

/// @title ScopeEnforcer
/// @notice Minimal EIP-7702 delegation target for scoped session keys.
/// Root EOA delegates to this contract. Session keys call execute().
/// Enforces: msg.sender==granted session, expiry, dailyCap, whitelist.
contract ScopeEnforcer {
    // The EOA address (address(this) after delegation)
    address public immutable self;

    struct Scope {
        uint256 dailyCap;      // in wei
        uint256 spentToday;    // in wei
        uint256 lastDay;       // unix day
        uint64 expiry;         // timestamp
        mapping(address => bool) allowed;
    }

    mapping(address => Scope) public scopes; // session address => scope

    constructor() {
        self = address(this);
    }

    modifier onlySelf() {
        require(msg.sender == address(this), "only EOA root");
        _;
    }

    /// @notice Grant or update a session scope. Callable only via root-signed tx (msg.sender == this).
    function setScope(
        address session,
        uint256 cap,
        uint64 exp,
        address[] calldata wl
    ) external onlySelf {
        Scope storage s = scopes[session];
        s.dailyCap = cap;
        s.expiry = exp;
        s.lastDay = block.timestamp / 1 days;
        s.spentToday = 0;
        // clear previous? simple: overwrite by setting new
        // For simplicity we just set; a revoke+set is used in practice
        for (uint256 i = 0; i < wl.length; i++) {
            s.allowed[wl[i]] = true;
        }
    }

    function revoke(address session) external onlySelf {
        delete scopes[session];
    }

    /// @notice Execute a call under session constraints. Called by session key.
    /// tx: from=session, to=EOA (delegated), data=execute(...)
    function execute(address to, uint256 value, bytes calldata data) external payable {
        Scope storage s = scopes[msg.sender];
        require(s.expiry != 0 && block.timestamp < s.expiry, "no/expired session");
        uint256 day = block.timestamp / 1 days;
        if (day > s.lastDay) {
            s.spentToday = 0;
            s.lastDay = day;
        }
        require(s.spentToday + value <= s.dailyCap, "daily cap exceeded");
        require(s.allowed[to], "recipient not whitelisted");
        s.spentToday += value;

        (bool success, ) = to.call{value: value}(data);
        require(success, "inner call failed");
    }

    // Accept ETH directly to the (delegated) EOA
    receive() external payable {}
}
