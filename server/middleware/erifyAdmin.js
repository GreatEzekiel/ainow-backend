const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET || 'ngx_alpha_jwt_secret_key_2026';

/**
 * Middleware: Verify Authorization token and ensure user has 'admin' privileges
 */
const verifyAdmin = (req, res, next) => {
    try {
        const authHeader = req.headers.authorization;

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            return res.status(401).json({
                success: false,
                message: 'Access Denied: Missing or malformed authentication token.'
            });
        }

        const token = authHeader.split(' ')[1];
        const decoded = jwt.verify(token, JWT_SECRET);

        // Attach decoded user payload to request object
        req.user = decoded;

        // Strict Role Guard Check
        if (req.user.role !== 'admin' && !req.user.isAdmin) {
            return res.status(403).json({
                success: false,
                message: 'Forbidden: Insufficient permissions. Admin access required.'
            });
        }

        next();
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            return res.status(401).json({
                success: false,
                message: 'Unauthorized: Authentication token has expired.'
            });
        }

        return res.status(401).json({
            success: false,
            message: 'Unauthorized: Invalid token signature.'
        });
    }
};

module.exports = verifyAdmin;