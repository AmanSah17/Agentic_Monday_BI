import React from 'react';
import { motion } from 'motion/react';

export const ThreeDScene = () => {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden z-0 opacity-20">
      {/* Subtle 3D-feeling background elements */}
      <motion.div 
        animate={{ 
          rotateX: [0, 10, 0],
          rotateY: [0, 360],
          scale: [1, 1.1, 1]
        }}
        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        className="absolute top-[-10%] right-[-10%] w-[600px] h-[600px] border border-primary/20 rounded-full perspective-1000 preserve-3d"
      >
        <div className="absolute inset-0 border border-primary/10 rounded-full rotate-45" />
        <div className="absolute inset-0 border border-primary/10 rounded-full -rotate-45" />
      </motion.div>

      <motion.div 
        animate={{ 
          y: [0, -50, 0],
          x: [0, 30, 0],
          rotate: [0, 90, 0]
        }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-[10%] left-[5%] w-64 h-64 bg-primary-container/5 blur-[100px] rounded-full"
      />
    </div>
  );
};
