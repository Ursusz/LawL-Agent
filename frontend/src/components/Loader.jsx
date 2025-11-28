import React from 'react';

function Loader() {
  return (
    <div
      className="fixed inset-0 flex items-center justify-center z-50"
      style={{
        backgroundImage: 'url("/background.jpg")',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    >
      {/* Dark overlay */}
      <div className="absolute inset-0 bg-black/20"></div>

      {/* Glassmorphic loader card */}
      <div
        className="relative z-10 rounded-3xl p-12"
        style={{
          backgroundColor: 'rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '2px solid rgba(255, 255, 255, 0.3)',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
        }}
      >
        <div className="flex flex-col items-center justify-center gap-6">
          <div
            className="loader ease-linear rounded-full border-8 h-24 w-24"
            style={{
              borderColor: 'rgba(255, 255, 255, 0.3)',
              borderTopColor: 'rgba(255, 255, 255, 0.9)',
              boxShadow: '0 0 20px rgba(255, 255, 255, 0.2)'
            }}
          ></div>
          <p className="text-lg font-semibold text-white drop-shadow-lg">
            Loading...
          </p>
        </div>
      </div>

      <style jsx>{`
        .loader {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export default Loader;