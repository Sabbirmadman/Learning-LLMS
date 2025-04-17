import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/hooks/useAuth';
import ThemeTogglebutton from '../ui/theme-togggle';
import { LogOut } from 'lucide-react';

// logo import from public folder
import logo from './../../assets/logo.png';

const Navbar = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="bg-background border-b">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 font-bold text-xl">
            <img src={logo} alt="ChatCraft" className="h-8" />
            <span className="hidden sm:inline">ChatCraft</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            {isAuthenticated && (
              <>
                <Link to="/myfiles" className="text-muted-foreground hover:text-foreground">My Files</Link>
                <Link to="/chat" className="text-muted-foreground hover:text-foreground">Chat</Link>
                <Link to="/profile" className="text-muted-foreground hover:text-foreground">Profile</Link>
                <Button variant="ghost" onClick={handleLogout}>
                  <LogOut size={16} />
                </Button>
              </>
            )}
            <ThemeTogglebutton />
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <ThemeTogglebutton />
            <button 
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="ml-2 p-2 rounded-md hover:bg-muted"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {isMenuOpen && (
          <div className="md:hidden py-4 space-y-3">
            {isAuthenticated ? (
              <>
                <Link to="/myfiles" className="block py-2 hover:bg-muted px-2 rounded">My Files</Link>
                <Link to="/chat" className="block py-2 hover:bg-muted px-2 rounded">Chat</Link>
                <Link to="/profile" className="block py-2 hover:bg-muted px-2 rounded">Profile</Link>
                <Button variant="outline" onClick={handleLogout} className="w-full">Logout</Button>
              </>
            ) : (
              <>
                <Link to="/login" className="block py-2 hover:bg-muted px-2 rounded">Login</Link>
                <Button asChild className="w-full">
                  <Link to="/signup">Sign Up</Link>
                </Button>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar;