# Frontend Dashboard

React/TypeScript dashboard for the AI CI/CD Platform. Part of [splinteredsunlight/ai-cicd-platform](https://github.com/splinteredsunlight/ai-cicd-platform).

## Features

- 📊 Real-time metrics and analytics
- 🔄 Pipeline management and monitoring
- 🛡️ Security vulnerability tracking
- 🔧 Self-healing debugger interface
- ⚙️ System configuration and settings

## Tech Stack

- React 18
- TypeScript
- Material UI
- Zustand (State Management)
- Vite (Build Tool)
- Nivo (Charts)
- React Router
- Axios

## Development Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Configure the following variables in `.env`:
   ```
   VITE_API_URL=http://localhost:8000
   VITE_ENABLE_DEBUG_MODE=true
   VITE_ENABLE_ANALYTICS=false
   VITE_APP_NAME="AI CI/CD Platform"
   VITE_DEFAULT_THEME=light
   VITE_POLLING_INTERVAL=30000
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Access the dashboard:
   - URL: http://localhost:3000
   - Development credentials:
     - Email: admin@example.com
     - Password: admin123

## Project Structure

```
src/
├── config/           # Configuration files
│   ├── api.ts       # API endpoints and types
│   └── theme.ts     # MUI theme configuration
├── layouts/         # Page layouts
│   ├── AuthLayout/  # Authentication pages layout
│   └── MainLayout/  # Main application layout
├── pages/          # Application pages
│   ├── auth/       # Authentication pages
│   ├── dashboard/  # Dashboard and analytics
│   ├── pipelines/  # Pipeline management
│   ├── security/   # Security monitoring
│   ├── debugger/   # Self-healing debugger
│   └── settings/   # System settings
├── stores/         # State management
│   ├── auth.store.ts    # Authentication state
│   ├── metrics.store.ts # Analytics state
│   ├── pipeline.store.ts # Pipeline state
│   ├── security.store.ts # Security state
│   └── debug.store.ts   # Debugger state
└── components/     # Reusable components
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run test` - Run tests
- `npm run coverage` - Generate test coverage report

## Development Guidelines

1. **TypeScript**:
   - Use strict type checking
   - Define interfaces for all data structures
   - Avoid using `any` type

2. **State Management**:
   - Use Zustand for global state
   - Keep component state local when possible
   - Use React Query for server state

3. **Styling**:
   - Use Material UI's `sx` prop for styling
   - Follow theme configuration
   - Maintain consistent spacing

4. **Components**:
   - Keep components focused and reusable
   - Use TypeScript interfaces for props
   - Document complex components

5. **Testing**:
   - Write unit tests for critical components
   - Test state management logic
   - Mock API calls in tests

## Production Deployment

1. Build the application:
   ```bash
   npm run build
   ```

2. Configure production environment:
   - Set `VITE_API_URL` to production API URL
   - Disable debug mode
   - Configure proper authentication

3. Deploy the `dist` directory to your hosting service

## Monitoring and Analytics

The dashboard includes built-in monitoring:

- Real-time metrics tracking
- Error logging
- Performance monitoring
- User activity tracking

## Troubleshooting

Common issues and solutions:

1. **API Connection Issues**:
   - Verify API URL in `.env`
   - Check API service status
   - Confirm CORS configuration

2. **Authentication Issues**:
   - Clear localStorage
   - Check token expiration
   - Verify API credentials

3. **Performance Issues**:
   - Check polling intervals
   - Monitor browser console
   - Review network requests

## Contributing

1. Follow TypeScript best practices
2. Maintain consistent code style
3. Write clear commit messages
4. Add/update tests as needed
5. Document changes

## License

MIT License - see the main project LICENSE file for details.
