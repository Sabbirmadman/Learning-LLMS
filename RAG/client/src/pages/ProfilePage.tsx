import React from 'react';

const ProfilePage: React.FC = () => {
  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Profile</h1>
      
      <div className="bg-card p-6 rounded-lg shadow-md">
        {/* Profile Header */}
        <div className="flex items-center gap-6 mb-8">
          <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center text-4xl">
            <span>JD</span>
          </div>
          <div>
            <h2 className="text-xl font-bold">John Doe</h2>
            <p className="text-muted-foreground">john.doe@example.com</p>
            <button className="mt-2 text-primary text-sm hover:underline">Change profile picture</button>
          </div>
        </div>
        
        {/* Profile Form */}
        <form className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="firstName" className="block text-sm font-medium">First Name</label>
              <input 
                type="text" 
                id="firstName" 
                defaultValue="John"
                className="w-full p-2 border rounded-md"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="lastName" className="block text-sm font-medium">Last Name</label>
              <input 
                type="text" 
                id="lastName" 
                defaultValue="Doe"
                className="w-full p-2 border rounded-md"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="email" className="block text-sm font-medium">Email</label>
              <input 
                type="email" 
                id="email" 
                defaultValue="john.doe@example.com"
                className="w-full p-2 border rounded-md"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="phone" className="block text-sm font-medium">Phone Number</label>
              <input 
                type="tel" 
                id="phone" 
                defaultValue="(555) 123-4567"
                className="w-full p-2 border rounded-md"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <label htmlFor="bio" className="block text-sm font-medium">Bio</label>
            <textarea 
              id="bio" 
              rows={4}
              defaultValue="Software developer with 5 years of experience in web development."
              className="w-full p-2 border rounded-md"
            ></textarea>
          </div>
          
          <div className="pt-4 border-t flex justify-end gap-4">
            <button 
              type="button" 
              className="px-4 py-2 border rounded-md hover:bg-muted"
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProfilePage;
